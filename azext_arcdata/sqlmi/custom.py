# ------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# ------------------------------------------------------------------------------

import base64
import json
import os
import shutil
import sys
import time
from datetime import datetime

import azext_arcdata.core.kubernetes as kubernetes_util
import yaml

from azext_arcdata.core.arcdata_cli_credentials import ArcDataCliCredential
from azext_arcdata.core.constants import (
    ARC_GROUP,
    AZDATA_PASSWORD,
    AZDATA_USERNAME,
    CERT_ARGUMENT_ERROR_TEMPLATE,
    DATA_CONTROLLER_CRD_VERSION,
    DATA_CONTROLLER_PLURAL,
    USE_K8S_EXCEPTION_TEXT,
)
from azext_arcdata.core.prompt import prompt, prompt_pass
from azext_arcdata.core.util import (
    FileUtil,
    check_and_set_kubectl_context,
    get_config_from_template,
    is_windows,
    retry,
    parse_cert_files
)
from azext_arcdata.kubernetes_sdk.util import (
    validate_certificate_secret, 
    create_certificate_secret,
    check_secret_exists_with_retries
)
from azext_arcdata.kubernetes_sdk.dc.constants import (
    DAG_CRD_NAME,
    DATA_CONTROLLER_CRD_NAME,
    SQLMI_CRD,
    SQLMI_CRD_NAME,
)
from azext_arcdata.kubernetes_sdk.client import (
    K8sApiException,
    KubernetesClient,
    KubernetesError,
    http_status_codes,
)
from azext_arcdata.kubernetes_sdk.models.custom_resource import CustomResource
from azext_arcdata.kubernetes_sdk.models.data_controller_custom_resource import (
    DataControllerCustomResource,
)
from azext_arcdata.sqlmi.constants import (
    API_GROUP,
    API_VERSION,
    DAG_API_GROUP,
    DAG_API_VERSION,
    DAG_RESOURCE_KIND,
    DAG_RESOURCE_KIND_PLURAL,
    RESOURCE_KIND,
    RESOURCE_KIND_PLURAL,
    SQLMI_LICENSE_TYPE_DEFAULT,
    SQLMI_SPEC,
    SQLMI_TIER_BUSINESS_CRITICAL,
    SQLMI_TIER_BUSINESS_CRITICAL_SHORT,
    SQLMI_TIER_DEFAULT,
    SQLMI_TIER_GENERAL_PURPOSE,
)
from azext_arcdata.sqlmi.exceptions import SqlmiError
from azext_arcdata.sqlmi.models.dag_cr import DagCustomResource
from azext_arcdata.sqlmi.models.sqlmi_cr_model import SqlmiCustomResource
from azext_arcdata.sqlmi.sqlmi_utilities import upgrade_sqlmi_instances
from azext_arcdata.sqlmi.util import (
    CONNECTION_RETRY_ATTEMPTS,
    RETRY_INTERVAL,
    is_valid_connectivity_mode,
    is_valid_sql_password,
    validate_admin_login_secret,
    validate_labels_and_annotations,
)
from humanfriendly.terminal.spinners import AutomaticSpinner
from knack.cli import CLIError
from knack.log import get_logger
from urllib3.exceptions import MaxRetryError, NewConnectionError

logger = get_logger(__name__)


def arc_sql_mi_create(
    client,
    name,
    path=None,
    replicas=None,
    cores_limit=None,
    cores_request=None,
    memory_limit=None,
    memory_request=None,
    storage_class_data=None,
    storage_class_logs=None,
    storage_class_datalogs=None,
    storage_class_backups=None,
    volume_size_data=None,
    volume_size_logs=None,
    volume_size_datalogs=None,
    volume_size_backups=None,
    no_wait=False,
    license_type=None,
    tier=None,
    dev=None,
    # -- indirect --
    namespace=None,
    use_k8s=None,
    noexternal_endpoint=None,
    certificate_public_key_file=None,
    certificate_private_key_file=None,
    service_certificate_secret=None,
    admin_login_secret=None,
    labels=None,
    annotations=None,
    service_labels=None,
    service_annotations=None,
    storage_labels=None,
    storage_annotations=None,
    collation=None,
    language=None,
    agent_enabled=None,
    trace_flags=None,
    time_zone=None,
    retention_days=None,
    # -- direct --
    location=None,
    custom_location=None,
    resource_group=None,
):
    """
    Create a SQL managed instance.
    """

    args = locals()

    try:
        if not use_k8s:
            from azext_arcdata.arm_sdk.client import ArmClient

            cred = ArcDataCliCredential()
            subscription = client.subscription
            armclient = ArmClient(
                azure_credential=cred, subscription_id=subscription
            )

            poller = armclient.create_sqlmi(
                name=name,
                path=path,
                replicas=replicas,
                cores_limit=cores_limit,
                cores_request=cores_request,
                memory_limit=memory_limit,
                memory_request=memory_request,
                storage_class_data=storage_class_data,
                storage_class_logs=storage_class_logs,
                storage_class_datalogs=storage_class_datalogs,
                storage_class_backups=storage_class_backups,
                volume_size_data=volume_size_data,
                volume_size_logs=volume_size_logs,
                volume_size_datalogs=volume_size_datalogs,
                volume_size_backups=volume_size_backups,
                license_type=license_type,
                tier=tier,
                dev=dev,
                location=location,
                custom_location=custom_location,
                resource_group=resource_group,
                polling=not no_wait,
            )

            return poller

        check_and_set_kubectl_context()
        namespace = client.namespace

        rd = 7 if retention_days is None else retention_days
        # Determine source for the resource spec preferring path first
        #
        if not path:
            # TODO: Use mutating web hooks to set these default values
            #
            spec_object = {
                "apiVersion": API_GROUP
                + "/"
                + KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                "kind": RESOURCE_KIND,
                "metadata": {},
                "spec": {
                    "forceHA": "true",
                    "backup": {
                        "retentionPeriodInDays": rd,
                    },
                    "tier": SQLMI_TIER_DEFAULT,
                    "licenseType": SQLMI_LICENSE_TYPE_DEFAULT,
                    "storage": {
                        "data": {"volumes": [{"size": "5Gi"}]},
                        "logs": {"volumes": [{"size": "5Gi"}]},
                    },
                },
            }

        # Otherwise, use the provided azext_arcdata file.
        #
        else:
            spec_object = FileUtil.read_json(path)

        # Decode base spec and apply args. Must patch namespace in separately
        # since it's not parameterized in this func
        cr = CustomResource.decode(SqlmiCustomResource, spec_object)
        cr.metadata.namespace = namespace
        cr.apply_args(**args)
        cr.validate(client.apis.kubernetes)

        # If tier is provided and not replicas, then default replicas based on
        #  given tier value
        #
        if tier:
            if not replicas:
                if (tier == SQLMI_TIER_BUSINESS_CRITICAL) or (
                    tier == SQLMI_TIER_BUSINESS_CRITICAL_SHORT
                ):
                    cr.spec.replicas = 3

        if replicas:
            try:
                cr.spec.replicas = int(replicas)

                # Set the tier based on specfied replicas. With fail safe
                # validation enabled, it will go in error if user specifies
                # incorrect value.
                #
                if not tier:
                    if cr.spec.replicas == 1:
                        cr.spec.tier = SQLMI_TIER_GENERAL_PURPOSE
                    else:
                        cr.spec.tier = SQLMI_TIER_BUSINESS_CRITICAL
            except ValueError as e:
                raise CLIError(e)

        validate_labels_and_annotations(
            labels,
            annotations,
            service_labels,
            service_annotations,
            storage_labels,
            storage_annotations,
        )

        custom_object_exists = retry(
            lambda: client.apis.kubernetes.namespaced_custom_object_exists(
                name,
                namespace,
                group=API_GROUP,
                version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                plural=RESOURCE_KIND_PLURAL,
            ),
            retry_count=CONNECTION_RETRY_ATTEMPTS,
            retry_delay=RETRY_INTERVAL,
            retry_method="get namespaced custom object",
            retry_on_exceptions=(
                NewConnectionError,
                MaxRetryError,
                KubernetesError,
            ),
        )
        if custom_object_exists:
            raise ValueError(
                "Arc SQL managed instance `{}` already exists in namespace "
                "`{}`.".format(name, namespace)
            )

        if not noexternal_endpoint:
            response = retry(
                lambda: client.apis.kubernetes.list_namespaced_custom_object(
                    namespace,
                    group=ARC_GROUP,
                    version=KubernetesClient.get_crd_version(
                        DATA_CONTROLLER_CRD_NAME
                    ),
                    plural=DATA_CONTROLLER_PLURAL,
                ),
                retry_count=CONNECTION_RETRY_ATTEMPTS,
                retry_delay=RETRY_INTERVAL,
                retry_method="list namespaced custom object",
                retry_on_exceptions=(
                    NewConnectionError,
                    MaxRetryError,
                    K8sApiException,
                ),
            )

            dcs = response.get("items")
            if not dcs:
                raise CLIError(
                    "No data controller exists in namespace `{}`. Cannot set "
                    "external endpoint argument.".format(namespace)
                )
            else:
                is_valid_connectivity_mode(client)
                dc_cr = CustomResource.decode(
                    DataControllerCustomResource, dcs[0]
                )
                cr.spec.services.primary.serviceType = (
                    dc_cr.get_controller_service().serviceType
                )

        # Create admin login secret
        #
        if not admin_login_secret:
            # Use default secret name when the user does not provide one.
            #
            admin_login_secret = name + "-login-secret"

        # Stamp the secret name on the custom resource.
        #
        cr.spec.security.adminLoginSecret = admin_login_secret

        login_secret_exists = check_secret_exists_with_retries(
            client.apis.kubernetes, cr.metadata.namespace, admin_login_secret
        )

        if login_secret_exists:
            # Validate that the existing login secret has correct format.
            #
            validate_admin_login_secret(
                client, cr.metadata.namespace, admin_login_secret
            )
        else:
            username, pw = _get_user_pass(client, name)

            secrets = dict()
            encoding = "utf-8"
            secrets["secretName"] = admin_login_secret
            secrets["base64Username"] = base64.b64encode(
                bytes(username, encoding)
            ).decode(encoding)
            secrets["base64Password"] = base64.b64encode(
                bytes(pw, encoding)
            ).decode(encoding)
            temp = get_config_from_template(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "templates",
                    "useradmin-login.yaml.tmpl",
                ),
                secrets,
            )
            mssql_secret = yaml.safe_load(temp)

            try:
                retry(
                    lambda: client.apis.kubernetes.create_secret(
                        cr.metadata.namespace,
                        mssql_secret,
                        ignore_conflict=True,
                    ),
                    retry_count=CONNECTION_RETRY_ATTEMPTS,
                    retry_delay=RETRY_INTERVAL,
                    retry_method="create secret",
                    retry_on_exceptions=(
                        NewConnectionError,
                        MaxRetryError,
                        K8sApiException,
                    ),
                )

            except K8sApiException as e:
                if e.status != http_status_codes.conflict:
                    raise

        # Create service certificate based on parameters
        #
        _create_service_certificate(
            client,
            cr,
            name,
            certificate_public_key_file,
            certificate_private_key_file,
            service_certificate_secret
        )

        # Create custom resource.
        #
        retry(
            lambda: client.apis.kubernetes.create_namespaced_custom_object(
                cr=cr, plural=RESOURCE_KIND_PLURAL, ignore_conflict=True
            ),
            retry_count=CONNECTION_RETRY_ATTEMPTS,
            retry_delay=RETRY_INTERVAL,
            retry_method="create namespaced custom object",
            retry_on_exceptions=(
                NewConnectionError,
                MaxRetryError,
                KubernetesError,
            ),
        )

        if no_wait:
            client.stdout(
                "Deployed {0} in namespace `{1}`. Please use `az sql mi-arc "
                "show -n {0} --k8s-namespace {1} --use-k8s` to check its "
                "status.".format(cr.metadata.name, cr.metadata.namespace)
            )
        else:
            response = retry(
                lambda: client.apis.kubernetes.get_namespaced_custom_object(
                    cr.metadata.name,
                    cr.metadata.namespace,
                    group=API_GROUP,
                    version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                    plural=RESOURCE_KIND_PLURAL,
                ),
                retry_count=CONNECTION_RETRY_ATTEMPTS,
                retry_delay=RETRY_INTERVAL,
                retry_method="get namespaced custom object",
                retry_on_exceptions=(
                    NewConnectionError,
                    MaxRetryError,
                    KubernetesError,
                ),
            )
            deployed_cr = CustomResource.decode(SqlmiCustomResource, response)
            get_namespaced_custom_object = (
                client.apis.kubernetes.get_namespaced_custom_object
            )

            if not is_windows():
                with AutomaticSpinner(
                    "Deploying {0} in namespace `{1}`".format(
                        cr.metadata.name, cr.metadata.namespace
                    ),
                    show_time=True,
                ):
                    while not _is_instance_ready(deployed_cr):
                        if _is_instance_in_error(deployed_cr):
                            client.stdout(
                                "{0} is in error state: {1}".format(
                                    cr.metadata.name,
                                    _get_error_message(deployed_cr),
                                )
                            )
                            break

                        time.sleep(5)
                        response = retry(
                            lambda: get_namespaced_custom_object(
                                cr.metadata.name,
                                cr.metadata.namespace,
                                group=API_GROUP,
                                version=KubernetesClient.get_crd_version(
                                    SQLMI_CRD_NAME
                                ),
                                plural=RESOURCE_KIND_PLURAL,
                            ),
                            retry_count=CONNECTION_RETRY_ATTEMPTS,
                            retry_delay=RETRY_INTERVAL,
                            retry_method="get namespaced custom object",
                            retry_on_exceptions=(
                                NewConnectionError,
                                MaxRetryError,
                                KubernetesError,
                            ),
                        )

                        deployed_cr = CustomResource.decode(
                            SqlmiCustomResource, response
                        )
            else:
                client.stdout(
                    "Deploying {0} in namespace `{1}`".format(name, namespace)
                )
                while not _is_instance_ready(deployed_cr):
                    if _is_instance_in_error(deployed_cr):
                        client.stdout(
                            "{0} is in error state: {1}".format(
                                cr.metadata.name,
                                _get_error_message(deployed_cr),
                            )
                        )
                        break

                    time.sleep(5)
                    response = retry(
                        lambda: get_namespaced_custom_object(
                            cr.metadata.name,
                            cr.metadata.namespace,
                            group=API_GROUP,
                            version=KubernetesClient.get_crd_version(
                                SQLMI_CRD_NAME
                            ),
                            plural=RESOURCE_KIND_PLURAL,
                        ),
                        retry_count=CONNECTION_RETRY_ATTEMPTS,
                        retry_delay=RETRY_INTERVAL,
                        retry_method="get namespaced custom object",
                        retry_on_exceptions=(
                            NewConnectionError,
                            MaxRetryError,
                            KubernetesError,
                        ),
                    )

                    deployed_cr = CustomResource.decode(
                        SqlmiCustomResource, response
                    )

            if _is_instance_ready(deployed_cr):
                client.stdout("{0} is Ready".format(cr.metadata.name))

    except KubernetesError as e:
        raise SqlmiError(e.message)
    except ValueError as e:
        raise CLIError(e)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_upgrade(
    client,
    namespace=None,
    name=None,
    field_filter=None,
    label_filter=None,
    desired_version=None,
    dry_run=None,
    force=False,
    use_k8s=None,
    resource_group=None,
    no_wait=False,
):
    if name is None and field_filter is None and label_filter is None:
        raise CLIError(
            "One of the following parameters is "
            "required: --name, --field-filter, --label-filter"
        )

    try:
        if not use_k8s:
            from azext_arcdata.arm_sdk.client import ArmClient

            if name is None:
                raise CLIError(
                    "Parameter --name must be used for connected mode upgrades"
                )

            cred = ArcDataCliCredential()
            subscription = client.subscription
            armclient = ArmClient(
                azure_credential=cred, subscription_id=subscription
            )

            armclient.upgrade_sqlmi(
                resource_group, name, desired_version, no_wait
            )

        else:
            upgrade_sqlmi_instances(
                namespace,
                name,
                field_filter,
                label_filter,
                desired_version,
                dry_run,
                force,
                use_k8s,
            )
    except KubernetesError as e:
        raise SqlmiError(e.message)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_edit(
    client,
    name,
    namespace=None,
    path=None,
    cores_limit=None,
    cores_request=None,
    memory_limit=None,
    memory_request=None,
    nowait=False,
    dev=None,
    labels=None,
    annotations=None,
    service_labels=None,
    service_annotations=None,
    agent_enabled=None,
    trace_flags=None,
    time_zone=None,
    use_k8s=None,
    retention_days=None,
    # -- direct --
    location=None,
    custom_location=None,
    resource_group=None,
    tag_name=None,
    tag_value=None,
):
    """
    Deprecated, use update over edit.
    """
    try:
        if False:
            from azext_arcdata.arm_sdk.client import ArmClient

            cred = ArcDataCliCredential()
            subscription = client.subscription
            armclient = ArmClient(
                azure_credential=cred, subscription_id=subscription
            )

            # Update the path or the latest cloud template
            #
            if path:
                with open(path, encoding="utf-8") as input_file:
                    prop = json.load(input_file)
            else:
                response = arc_sql_mi_show(client, name, resource_group)
                prop = {
                    "properties": {},
                }
                prop["properties"]["k8sRaw"] = response["properties"][
                    "k8_s_raw"
                ]
                prop["sku"] = response["sku"]
                # Tag is not supported for now
                #
                # prop["tags"] = response["tags"]
                k8s = prop["properties"]["k8sRaw"]

            cores_limit_flag = False
            cores_request_flag = False
            memory_limit_flag = False
            memory_request_flag = False
            dev_flag = False
            agent_enabled_flag = False
            time_zone_flag = False
            retention_days_flag = False
            labels_flag = False
            annotations_flag = False
            service_labels_flag = False
            service_annotations_flag = False
            if (
                cores_limit
                and cores_limit
                != prop["properties"]["k8sRaw"]["spec"]["scheduling"][
                    "default"
                ]["resources"]["limits"]["cpu"]
            ):
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["limits"]["cpu"] = cores_limit
                cores_limit_flag = True
            if (
                cores_request
                and cores_request
                != prop["properties"]["k8sRaw"]["spec"]["scheduling"][
                    "default"
                ]["resources"]["requests"]["cpu"]
            ):
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["requests"]["cpu"] = cores_request
                cores_request_flag = True
            if (
                memory_limit
                and memory_limit
                != prop["properties"]["k8sRaw"]["spec"]["scheduling"][
                    "default"
                ]["resources"]["limits"]["memory"]
            ):
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["limits"]["memory"] = memory_limit
                memory_limit_flag = True
            if (
                memory_request
                and memory_request
                != prop["properties"]["k8sRaw"]["spec"]["scheduling"][
                    "default"
                ]["resources"]["requests"]["memory"]
            ):
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["requests"]["memory"] = memory_request
                memory_request_flag = True
            if (
                agent_enabled
                and agent_enabled
                != prop["properties"]["k8sRaw"]["spec"]["settings"]["sqlagent"][
                    "enabled"
                ]
            ):
                prop["properties"]["k8sRaw"]["spec"]["settings"]["sqlagent"][
                    "enabled"
                ] = agent_enabled
                agent_enabled_flag = True
            if (
                time_zone
                and time_zone
                != prop["properties"]["k8sRaw"]["spec"]["settings"]["timezone"]
            ):
                prop["properties"]["k8sRaw"]["spec"]["settings"][
                    "timezone"
                ] = time_zone
                time_zone_flag = True
            if (
                retention_days
                and retention_days
                != prop["properties"]["k8sRaw"]["spec"]["backup"][
                    "retentionPeriodInDays"
                ]
            ):
                prop["properties"]["k8sRaw"]["spec"]["backup"][
                    "retentionPeriodInDays"
                ] = retention_days
                retention_days_flag = True
            if trace_flags:
                prop["properties"]["k8sRaw"]["spec"]["settings"][
                    "traceFlags"
                ] = trace_flags
            if labels:
                prop["properties"]["k8sRaw"]["spec"]["metadata"][
                    "labels"
                ] = labels
                labels_flag = True
            if annotations:
                prop["properties"]["k8sRaw"]["spec"]["metadata"][
                    "annotations"
                ] = annotations
                annotations_flag = True
            if service_labels:
                prop["properties"]["k8sRaw"]["spec"]["services"]["primary"][
                    "labels"
                ] = service_labels
                service_labels_flag = True
            if service_annotations:
                prop["properties"]["k8sRaw"]["spec"]["services"]["primary"][
                    "annotations"
                ] = service_annotations
                service_annotations_flag = True

            # dev key should be bool, but was logged str. Need further debug.
            #
            # if dev and dev != prop["properties"]["k8sRaw"]["spec"]["dev"]:
            #     prop["properties"]["k8sRaw"]["spec"]["dev"] = dev
            #     dev_flag = True

            # --- currently not supported by cloud side ---
            # Other items which are either disappeared in the
            # sqlmi_cr_model or azure.liquid template
            #
            # if preferred_primary_replica:
            #     prop["properties"]["k8sRaw"]["spec"][
            #         "preferredPrimaryReplica"
            #     ] = preferred_primary_replica
            # if preferred_primary_replica:
            #     prop["properties"]["k8sRaw"]["spec"][
            #         "primaryReplicaFailoverInterval"
            #     ] = primary_replica_failover_interval
            # if tag_name and tag_value:
            #     update_Content = {"tags": {tag_name: tag_value}}
            #     poller = armclient.patch_sqlmi(
            #         rg_name=resource_group,
            #         sqlmi_name=name,
            #         properties=update_Content,
            #     )

            poller = None
            if (
                cores_limit_flag
                or cores_request_flag
                or memory_limit_flag
                or memory_request_flag
                # Below are the keys are missing in the portal
                #
                # or preferred_primary_replica
                # or primary_replica_failover_interval
                # Below are the flags which may crash the status key
                # in the portal response and also won't change the
                # cluster status. Need further check to enable
                #
                # or labels_flag
                # or annotations_flag
                # or service_labels_flag
                # or service_annotations_flag
                # or trace_flags
                # or dev_flag
                # or time_zone_flag
                # or agent_enabled_flag
                # or retention_days_flag
            ):
                return armclient.create_sqlmi(
                    name=name,
                    location=location,
                    custom_location=custom_location,
                    resource_group=resource_group,
                    namespace=k8s["spec"]["metadata"]["namespace"],
                    path=path,
                    replicas=k8s["spec"]["replicas"],
                    cores_limit=k8s["spec"]["scheduling"]["default"][
                        "resources"
                    ]["limits"]["cpu"],
                    cores_request=k8s["spec"]["scheduling"]["default"][
                        "resources"
                    ]["requests"]["cpu"],
                    memory_limit=k8s["spec"]["scheduling"]["default"][
                        "resources"
                    ]["limits"]["memory"],
                    memory_request=k8s["spec"]["scheduling"]["default"][
                        "resources"
                    ]["requests"]["memory"],
                    storage_class_data=k8s["spec"]["storage"]["data"][
                        "volumes"
                    ][0]["className"],
                    storage_class_logs=k8s["spec"]["storage"]["logs"][
                        "volumes"
                    ][0]["className"],
                    storage_class_datalogs=k8s["spec"]["storage"]["datalogs"][
                        "volumes"
                    ][0]["className"],
                    storage_class_backups=k8s["spec"]["storage"]["backups"][
                        "volumes"
                    ][0]["className"],
                    volume_size_data=k8s["spec"]["storage"]["data"]["volumes"][
                        0
                    ]["size"],
                    volume_size_logs=k8s["spec"]["storage"]["logs"]["volumes"][
                        0
                    ]["size"],
                    volume_size_datalogs=k8s["spec"]["storage"]["datalogs"][
                        "volumes"
                    ][0]["size"],
                    volume_size_backups=k8s["spec"]["storage"]["backups"][
                        "volumes"
                    ][0]["size"],
                    no_wait=nowait,
                    noexternal_endpoint=None,
                    certificate_public_key_file=None,
                    certificate_private_key_file=None,
                    service_certificate_secret=None,
                    admin_login_secret=None,
                    license_type=response["properties"]["license_type"],
                    tier=k8s["spec"]["tier"],
                    dev=dev,
                    labels=k8s["spec"]["metadata"]["labels"],
                    annotations=k8s["spec"]["metadata"]["annotations"],
                    service_labels=k8s["spec"]["services"]["primary"]["labels"],
                    service_annotations=k8s["spec"]["services"]["primary"][
                        "annotations"
                    ],
                    storage_labels=None,
                    storage_annotations=None,
                    use_k8s=None,
                    collation=k8s["spec"]["settings"]["collation"],
                    language=k8s["spec"]["settings"]["language"],
                    agent_enabled=k8s["spec"]["settings"]["sqlagent"][
                        "enabled"
                    ],
                    trace_flags=k8s["spec"]["settings"]["traceFlags"],
                    time_zone=k8s["spec"]["settings"]["timezone"],
                    retention_days=k8s["spec"]["backup"][
                        "retentionPeriodInDays"
                    ],
                    polling=not nowait,
                )
        else:
            arc_sql_mi_update(
                client,
                name,
                namespace=namespace,
                path=path,
                cores_limit=cores_limit,
                cores_request=cores_request,
                memory_limit=memory_limit,
                memory_request=memory_request,
                no_wait=nowait,
                dev=dev,
                labels=labels,
                annotations=annotations,
                service_labels=service_labels,
                service_annotations=service_annotations,
                agent_enabled=agent_enabled,
                trace_flags=trace_flags,
                time_zone=time_zone,
                # preferred_primary_replica=preferred_primary_replica,
                # primary_replica_failover_interval=primary_replica_failover_interval,
                use_k8s=use_k8s,
                retention_days=retention_days,
                location=location,
                custom_location=custom_location,
                resource_group=resource_group,
                tag_name=tag_name,
                tag_value=tag_value,
            )
    except KubernetesError as e:
        raise SqlmiError(e.message)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_update(
    client,
    name,
    namespace=None,
    path=None,
    cores_limit=None,
    cores_request=None,
    memory_limit=None,
    memory_request=None,
    no_wait=False,
    dev=None,
    labels=None,
    annotations=None,
    service_labels=None,
    service_annotations=None,
    agent_enabled=None,
    trace_flags=None,
    time_zone=None,
    use_k8s=None,
    retention_days=None,
    certificate_public_key_file=None,
    certificate_private_key_file=None,
    service_certificate_secret=None,
    # -- direct --
    location=None,
    custom_location=None,
    resource_group=None,
    tag_name=None,
    tag_value=None,
):
    """
    Edit the configuration of a SQL managed instance.
    """
    if not use_k8s:
        raise ValueError(USE_K8S_EXCEPTION_TEXT)

    # -- currently not used, setting to empty --
    preferred_primary_replica = None
    primary_replica_failover_interval = None

    args = locals()

    def _check_replica_name(n, num_of_replicas, replica_name) -> bool:
        if replica_name == "any":
            return True
        x = replica_name.rfind("-")
        if x == -1:
            return False
        if replica_name[:x] != n:
            return False

        x += 1
        if int(replica_name[x:]) >= num_of_replicas:
            return False
        return True

    try:
        if not use_k8s:
            from azext_arcdata.arm_sdk.client import ArmClient
            from azext_arcdata.sqlmi.constants import (
                SQLMI_DIRECT_MODE_OUTPUT_SPEC,
                SQLMI_DIRECT_MODE_SPEC_MERGE,
            )

            cred = ArcDataCliCredential()
            subscription = client.subscription
            armclient = ArmClient(
                azure_credential=cred, subscription_id=subscription
            )

            loc = {"location": location}
            extendedLocation = (
                "/subscriptions/"
                + subscription
                + "/resourcegroups/"
                + resource_group
                + "/providers/microsoft.extendedlocation/customlocations/"
                + custom_location
            )
            exloc = {
                "extended_location": {
                    "name": extendedLocation,
                    "type": "CustomLocation",
                }
            }

            # Update the path or just the last created template
            config_file = path or os.path.join(SQLMI_DIRECT_MODE_OUTPUT_SPEC)
            with open(config_file, encoding="utf-8") as input_file:
                prop = json.load(input_file)

            if cores_limit:
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["limits"]["cpu"] = cores_limit
            if cores_request:
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["requests"]["cpu"] = cores_request
            if memory_limit:
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["limits"]["memory"] = memory_limit
            if memory_request:
                prop["properties"]["k8sRaw"]["spec"]["scheduling"]["default"][
                    "resources"
                ]["requests"]["memory"] = memory_request
            if dev:
                prop["properties"]["k8sRaw"]["spec"]["dev"] = dev
            if labels:
                prop["properties"]["k8sRaw"]["spec"]["metadata"][
                    "labels"
                ] = labels
            if annotations:
                prop["properties"]["k8sRaw"]["spec"]["metadata"][
                    "annotations"
                ] = annotations
            if service_labels:
                prop["properties"]["k8sRaw"]["spec"]["services"]["primary"][
                    "labels"
                ] = service_labels
            if service_annotations:
                prop["properties"]["k8sRaw"]["spec"]["services"]["primary"][
                    "annotations"
                ] = service_annotations
            if agent_enabled:
                prop["properties"]["k8sRaw"]["spec"]["settings"][
                    "agentEnabled"
                ] = agent_enabled
            if time_zone:
                prop["properties"]["k8sRaw"]["spec"]["settings"][
                    "timeZone"
                ] = time_zone
            if trace_flags:
                prop["properties"]["k8sRaw"]["spec"]["settings"][
                    "traceFlags"
                ] = trace_flags
            # Other items which are either disappeared in the
            # sqlmi_cr_model or azure.liquid template
            if retention_days:
                prop["properties"]["k8sRaw"]["spec"]["security"]["backup"][
                    "retentionPeriodInDays"
                ] = retention_days
            if tag_name and tag_value:
                poller = armclient.update_sqlmi(
                    rg_name=resource_group,
                    sqlmi_name=name,
                    properties={"tags": {tag_name: tag_value}},
                )
            if retention_days:
                prop["properties"]["k8sRaw"]["spec"]["security"]["backup"][
                    "retentionPeriodInDays"
                ] = retention_days
            if preferred_primary_replica:
                prop["properties"]["k8sRaw"]["spec"][
                    "preferredPrimaryReplica"
                ] = preferred_primary_replica
            if preferred_primary_replica:
                prop["properties"]["k8sRaw"]["spec"][
                    "primaryReplicaFailoverInterval"
                ] = primary_replica_failover_interval

            poller = None
            if (
                cores_limit
                or cores_request
                or memory_limit
                or memory_request
                or dev
                or labels
                or annotations
                or service_labels
                or service_annotations
                or agent_enabled
                or trace_flags
                or time_zone
                or preferred_primary_replica
                or primary_replica_failover_interval
                or use_k8s
                or retention_days
            ):
                poller = armclient.create_sqlmi(
                    name=name,
                    namespace=namespace,
                    path=path,
                    replicas=None,
                    cores_limit=cores_limit,
                    cores_request=cores_request,
                    memory_limit=memory_limit,
                    memory_request=memory_request,
                    storage_class_data=None,
                    storage_class_logs=None,
                    storage_class_datalogs=None,
                    storage_class_backups=None,
                    volume_size_data=None,
                    volume_size_logs=None,
                    volume_size_datalogs=None,
                    volume_size_backups=None,
                    no_wait=no_wait,
                    noexternal_endpoint=None,
                    certificate_public_key_file=None,
                    certificate_private_key_file=None,
                    service_certificate_secret=None,
                    admin_login_secret=None,
                    license_type=None,
                    tier=None,
                    dev=dev,
                    labels=labels,
                    annotations=annotations,
                    service_labels=service_labels,
                    service_annotations=service_annotations,
                    storage_labels=None,
                    storage_annotations=None,
                    use_k8s=use_k8s,
                    collation=None,
                    language=None,
                    agent_enabled=agent_enabled,
                    trace_flags=trace_flags,
                    time_zone=time_zone,
                    retention_days=retention_days,
                    location=location,
                    custom_location=custom_location,
                    resource_group=resource_group,
                    polling=not no_wait,
                )

                return poller

        check_and_set_kubectl_context()
        namespace = client.namespace

        if path:
            # Read azext_arcdata file for edit
            json_object = FileUtil.read_json(path)
        else:
            json_object = client.apis.kubernetes.get_namespaced_custom_object(
                name=name,
                namespace=namespace,
                group=API_GROUP,
                version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                plural=RESOURCE_KIND_PLURAL,
            )

        validate_labels_and_annotations(
            labels, annotations, service_labels, service_annotations, None, None
        )

        cr = CustomResource.decode(SqlmiCustomResource, json_object)

        cr.apply_args(**args)
        cr.validate(client.apis.kubernetes)

        if preferred_primary_replica:
            if not _check_replica_name(
                name,
                cr.spec.replicas,
                preferred_primary_replica,
            ):
                raise CLIError(
                    "Wrong pod name {0}".format(preferred_primary_replica)
                )
        else:
            preferred_primary_replica = "any"
        if not primary_replica_failover_interval:
            primary_replica_failover_interval = 600
        cr.spec.preferredPrimaryReplicaSpec.preferredPrimaryReplica = (
            preferred_primary_replica
        )
        cr.spec.preferredPrimaryReplicaSpec.primaryReplicaFailoverInterval = (
            int(primary_replica_failover_interval)
        )
        cr.spec.backup.retentionPeriodInDays = retention_days

        _create_service_certificate(
            client,
            cr,
            name,
            certificate_public_key_file,
            certificate_private_key_file,
            service_certificate_secret,
            is_update=True
        )

        # Patch CR
        client.apis.kubernetes.patch_namespaced_custom_object(
            cr=cr, plural=RESOURCE_KIND_PLURAL
        )

        if no_wait:
            client.stdout(
                "Updated {0} in namespace `{1}`. Please use `az sql mi-arc "
                "show -n {0} --k8s-namespace {1} --use-k8s` to check "
                "its status.".format(cr.metadata.name, cr.metadata.namespace)
            )
        else:
            response = client.apis.kubernetes.get_namespaced_custom_object(
                cr.metadata.name,
                cr.metadata.namespace,
                group=API_GROUP,
                version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                plural=RESOURCE_KIND_PLURAL,
            )
            deployed_cr = CustomResource.decode(SqlmiCustomResource, response)

            if not is_windows():
                with AutomaticSpinner(
                    "Updating {0} in namespace `{1}`".format(
                        cr.metadata.name, cr.metadata.namespace
                    ),
                    show_time=True,
                ):
                    while not _is_instance_ready(deployed_cr):
                        if _is_instance_in_error(deployed_cr):
                            client.stdout(
                                "{0} is in error state:{1}".format(
                                    cr.metadata.name,
                                    _get_error_message(deployed_cr),
                                )
                            )
                            break

                        time.sleep(5)
                        response = (
                            client.apis.kubernetes.get_namespaced_custom_object(
                                cr.metadata.name,
                                cr.metadata.namespace,
                                group=API_GROUP,
                                version=KubernetesClient.get_crd_version(
                                    SQLMI_CRD_NAME
                                ),
                                plural=RESOURCE_KIND_PLURAL,
                            )
                        )
                        deployed_cr = CustomResource.decode(
                            SqlmiCustomResource, response
                        )
            else:
                client.stdout(
                    "Updating {0} in namespace `{1}`".format(name, namespace)
                )
                while not _is_instance_ready(deployed_cr):
                    if _is_instance_in_error(deployed_cr):
                        client.stdout(
                            "{0} is in error state:{1}".format(
                                cr.metadata.name,
                                _get_error_message(deployed_cr),
                            )
                        )
                        break

                    time.sleep(5)
                    response = (
                        client.apis.kubernetes.get_namespaced_custom_object(
                            cr.metadata.name,
                            cr.metadata.namespace,
                            group=API_GROUP,
                            version=KubernetesClient.get_crd_version(
                                SQLMI_CRD_NAME
                            ),
                            plural=RESOURCE_KIND_PLURAL,
                        )
                    )
                    deployed_cr = CustomResource.decode(
                        SqlmiCustomResource, response
                    )

            if _is_instance_ready(deployed_cr):
                client.stdout("{0} is Ready".format(cr.metadata.name))

    except KubernetesError as e:
        raise SqlmiError(e.message)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_delete(
    client, name, resource_group=None, namespace=None, use_k8s=None
):
    """
    Delete a SQL managed instance.
    """
    try:

        if not use_k8s:
            from azext_arcdata.arm_sdk.client import ArmClient

            cred = ArcDataCliCredential()
            subscription = client.subscription
            armclient = ArmClient(
                azure_credential=cred, subscription_id=subscription
            )
            poller = armclient.delete_sqlmi(
                rg_name=resource_group, sqlmi_name=name
            )
            cnt = 0
            while True:
                if poller.status() == "Succeeded":
                    break
                elif poller.status() == "InProgress":
                    if cnt < 600:  # total wait time in seconds
                        time.sleep(5)
                        cnt += 5
                    else:
                        raise CLIError(poller.status())
                else:
                    raise CLIError(poller.status())
            return poller

        check_and_set_kubectl_context()
        is_valid_connectivity_mode(client)
        namespace = namespace or client.namespace

        client.apis.kubernetes.delete_namespaced_custom_object(
            name=name,
            namespace=namespace,
            group=API_GROUP,
            version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
            plural=RESOURCE_KIND_PLURAL,
        )

        client.stdout("Deleted {} from namespace {}".format(name, namespace))

    except KubernetesError as e:
        raise SqlmiError(e.message)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_show(
    client, name, resource_group=None, path=None, namespace=None, use_k8s=None
):

    """
    Show the details of a SQL managed instance.
    """
    try:
        if not use_k8s:
            from azext_arcdata.arm_sdk.client import ArmClient

            cred = ArcDataCliCredential()
            subscription = client.subscription
            arm_client = ArmClient(
                azure_credential=cred, subscription_id=subscription
            )

            response = arm_client.get_sqlmi(
                rg_name=resource_group, sqlmi_name=name
            )

            # state = poller.as_dict()["properties"]["provisioning_state"]
            # if state:
            #    return {"provisioningState": state}
        else:

            check_and_set_kubectl_context()
            namespace = namespace or client.namespace

            response = client.apis.kubernetes.get_namespaced_custom_object(
                name,
                namespace,
                group=API_GROUP,
                version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                plural=RESOURCE_KIND_PLURAL,
            )

        if path:
            if not os.path.isdir(path):
                os.makedirs(path)
            path = os.path.join(path, "{}.json".format(name))
            with open(path, "w") as outfile:
                json.dump(response, outfile, indent=4)
            client.stdout("{0} specification written to {1}".format(name, path))
        else:
            return response

    except KubernetesError as e:
        raise SqlmiError(e.message)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_getmirroringcert(
    client, name, cert_file, namespace=None, use_k8s=None
):

    args = locals()
    try:
        if not use_k8s:
            raise ValueError(USE_K8S_EXCEPTION_TEXT)

        check_and_set_kubectl_context()
        namespace = namespace or client.namespace

        json_object = client.apis.kubernetes.get_namespaced_custom_object(
            name=name,
            namespace=namespace,
            group=API_GROUP,
            version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
            plural=RESOURCE_KIND_PLURAL,
        )
        if not (cert_file):
            raise CLIError("cert_file cannot be null")

        cr = CustomResource.decode(SqlmiCustomResource, json_object)
        cr.apply_args(**args)
        cr.validate(client.apis.kubernetes)

        cr = CustomResource.decode(SqlmiCustomResource, json_object)
        if cr.spec.replicas > 1 or cr.spec.forceHA:
            config_map = kubernetes_util.get_config_map(
                namespace, "sql-config-{0}".format(name)
            )
            data_pem = config_map.data["sql-mirroring-cert"]
            client.stdout(
                "result write to file {0}: {1}".format(cert_file, data_pem)
            )

            file = open(cert_file, "w")
            file.write(data_pem)
            file.close()
        else:
            raise CLIError("More than 1 replica needed MIAA HA scenario.")
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_list(client, resource_group=None, namespace=None, use_k8s=None):
    """
    List SQL managed instances.
    """
    try:
        result = []
        if not use_k8s:
            from azext_arcdata.arm_sdk.client import ArmClient

            cred = ArcDataCliCredential()
            subscription = client.subscription
            armclient = ArmClient(
                azure_credential=cred, subscription_id=subscription
            )
            items = armclient.list_sqlmi(rg_name=resource_group)
            for item in items:
                result.append(item)
        else:
            check_and_set_kubectl_context()
            namespace = namespace or client.namespace

            response = client.apis.kubernetes.list_namespaced_custom_object(
                namespace,
                group=API_GROUP,
                version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                plural=RESOURCE_KIND_PLURAL,
            )
            items = response.get("items")
            # Temporary, need to discuss what the intended structure is across
            # partners
            for item in items:
                cr = CustomResource.decode(SqlmiCustomResource, item)
                result.append(
                    {
                        "name": cr.metadata.name,
                        "primaryEndpoint": cr.status.primaryEndpoint,
                        "replicas": cr.status.readyReplicas,
                        "state": cr.status.state,
                    }
                )

        return result

    except KubernetesError as e:
        raise SqlmiError(e.message)
    except Exception as e:
        raise CLIError(e)


def arc_sql_endpoint_list(client, name=None, namespace=None, use_k8s=None):
    """
    List endpoints for the given SQL managed instance(s).
    """
    try:

        if not use_k8s:
            raise ValueError(USE_K8S_EXCEPTION_TEXT)

        check_and_set_kubectl_context()

        namespace = namespace or client.namespace

        custom_resources = []

        if name:
            response = client.apis.kubernetes.get_namespaced_custom_object(
                name,
                namespace,
                group=API_GROUP,
                version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                plural=RESOURCE_KIND_PLURAL,
            )
            cr = CustomResource.decode(SqlmiCustomResource, response)
            if cr is None:
                raise CLIError(
                    "SQL managed instance {} not found.".format(name)
                )
            custom_resources.append(cr)
        else:
            response = client.apis.kubernetes.list_namespaced_custom_object(
                namespace,
                group=API_GROUP,
                version=KubernetesClient.get_crd_version(SQLMI_CRD_NAME),
                plural=RESOURCE_KIND_PLURAL,
            )

            items = response.get("items")

            for item in items:
                cr = CustomResource.decode(SqlmiCustomResource, item)
                if cr:
                    custom_resources.append(cr)

        arc_sql_endpoints = {"namespace": namespace}
        instances = []

        # Loop through the specified custom resources and retrieve their
        # endpoints from their status
        for cr in custom_resources:
            endpoints = []

            if cr.status:
                descrip_str = "description"
                endpoint_str = "endpoint"

                # Connection string
                ext_endpoint = cr.status.primaryEndpoint
                if ext_endpoint:
                    connection_str = ext_endpoint
                else:
                    connection_str = "Not yet available"
                endpoints.append(
                    {
                        descrip_str: "SQL Managed Instance",
                        endpoint_str: connection_str,
                    }
                )

                # Logs
                logs_endpoint = cr.status.log_search_dashboard
                endpoints.append(
                    {
                        descrip_str: "Log Search Dashboard",
                        endpoint_str: logs_endpoint,
                    }
                )

                # Metrics
                metrics_endpoint = cr.status.metrics_dashboard
                endpoints.append(
                    {
                        descrip_str: "Metrics Dashboard",
                        endpoint_str: metrics_endpoint,
                    }
                )

                # Readable Secondary Endpoint
                secondary_service_endpoint = cr.status.secondaryServiceEndpoint
                if secondary_service_endpoint:
                    endpoints.append(
                        {
                            descrip_str: "SQL Managed Instance Readable "
                            "Secondary Replicas",
                            endpoint_str: secondary_service_endpoint,
                        }
                    )

            instances.append({"name": cr.metadata.name, "endpoints": endpoints})

        arc_sql_endpoints["instances"] = instances

        return arc_sql_endpoints

    except KubernetesError as e:
        raise CLIError(e.message)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_config_init(client, path):
    """
    Returns a package of crd.json and spec-template.json.
    """
    try:
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)

        with open(SQLMI_CRD, "r") as stream:
            crd_content = yaml.safe_load(stream)
            crd_pretty = json.dumps(crd_content, indent=4)
            with open(os.path.join(path, "crd.json"), "w") as output:
                output.write(crd_pretty)

        # Copy spec.json template to the new path
        shutil.copy(SQLMI_SPEC, os.path.join(path, "spec.json"))

        client.stdout(
            "{0} templates created in directory: {1}".format(
                RESOURCE_KIND, path
            )
        )

    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_config_add(client, path, json_values):
    """
    Add new key and value to the given config file
    """
    try:
        client.add_configuration(path, json_values)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_config_replace(client, path, json_values):
    """
    Replace the value of a given key in the given config file
    """
    try:
        client.replace_configuration(path, json_values)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_config_remove(client, path, json_path):
    """
    Remove a key from the given config file
    """
    try:
        client.remove_configuration(path, json_path)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_config_patch(client, path, patch_file):
    """
    Patch a given file against the given config file
    """
    try:
        client.patch_configuration(path, patch_file)
    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_dag_create(
    client,
    name,
    dag_name,
    local_instance_name,
    local_primary,
    remote_instance_name,
    remote_mirroring_url,
    remote_mirroring_cert_file,
    namespace=None,
    path=None,
    use_k8s=None,
):
    args = locals()
    try:
        if not use_k8s:
            raise ValueError(USE_K8S_EXCEPTION_TEXT)
        check_and_set_kubectl_context()
        namespace = namespace or client.namespace

        # Determine source for the resource spec preferring path first
        #
        if not path:
            # TODO: Use mutating web hooks to set these default values
            #
            spec_object = {
                "apiVersion": DAG_API_GROUP + "/" + DAG_API_VERSION,
                "kind": DAG_RESOURCE_KIND,
                "metadata": {"name": name},
                "spec": {
                    "input": {
                        "dagName": dag_name,
                        "localName": local_instance_name,
                        "remoteName": remote_instance_name,
                        "remoteEndpoint": remote_mirroring_url,
                        "remotePublicCert": "",
                        "isLocalPrimary": local_primary,
                    }
                },
            }

        # Otherwise, use the provided src file.
        #
        else:
            spec_object = FileUtil.read_json(path)

        # Decode base spec and apply args. Must patch namespace in separately
        # since it's not parameterized in this func
        #
        cr = CustomResource.decode(DagCustomResource, spec_object)
        cr.metadata.namespace = namespace
        cr.validate(client.apis.kubernetes)

        file = open(remote_mirroring_cert_file, "r")
        remote_public_cert = file.read()
        file.close()

        cr.spec.input.remotePublicCert = remote_public_cert

        client.stdout(
            "create_namespaced_custom_object {0}".format(cr._to_dict())
        )

        if not is_windows():
            with AutomaticSpinner(
                "Deploying {0} in namespace `{1}`".format(
                    cr.metadata.name, cr.metadata.namespace
                ),
                show_time=True,
            ):
                state, results = client.create_dag(cr)
        else:
            client.stdout(
                "Deploying {0} in namespace `{1}`".format(
                    cr.metadata.name, cr.metadata.namespace
                )
            )

            state, results = client.create_dag(cr)

        client.stdout("{0} is Ready".format(cr.metadata.name))

        if state != "succeeded":
            raise CLIError(
                "Create Distributed AG return state({0}), result({1})".format(
                    state, results
                )
            )

    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_dag_delete(client, name, namespace=None, use_k8s=None):

    args = locals()
    try:
        if not use_k8s:
            raise ValueError(USE_K8S_EXCEPTION_TEXT)
        check_and_set_kubectl_context()
        namespace = namespace or client.namespace

        if not (name):
            raise CLIError("name {0} cannot be null".format(name))

        client.apis.kubernetes.delete_namespaced_custom_object(
            name=name,
            namespace=namespace,
            group=DAG_API_GROUP,
            version=KubernetesClient.get_crd_version(DAG_CRD_NAME),
            plural=DAG_RESOURCE_KIND_PLURAL,
        )
        client.stdout(
            "Deleted dag {} from namespace {}".format(name, namespace)
        )

    except Exception as e:
        raise CLIError(e)


def arc_sql_mi_dag_show(client, name, namespace=None, use_k8s=None):
    try:
        if not use_k8s:
            raise ValueError(USE_K8S_EXCEPTION_TEXT)
        check_and_set_kubectl_context()
        namespace = namespace or client.namespace
        response = client.apis.kubernetes.get_namespaced_custom_object(
            name,
            namespace,
            group=DAG_API_GROUP,
            version=KubernetesClient.get_crd_version(DAG_CRD_NAME),
            plural=DAG_RESOURCE_KIND_PLURAL,
        )
        cr = CustomResource.decode(DagCustomResource, response)
        client.stdout(
            "input: {}".format(json.dumps(cr.spec.input._to_dict(), indent=4))
        )
        client.stdout(
            "status: {}".format(json.dumps(cr.status._to_dict(), indent=4))
        )
    except Exception as e:
        raise CLIError(e)


def _is_instance_ready(cr):
    """
    Verify that the SQL Mi instance is ready
    :param cr: Instance to check the readiness of
    :return: True if the instance is ready, False otherwise
    """
    return cr.metadata.generation == cr.status.observed_generation and (
        cr.status.state is not None and cr.status.state.lower() == "ready"
    )


def _is_instance_in_error(cr):
    """
    Check that the SQL Mi instance is in error state
    :param cr: Instance to check the readiness of
    :return: True if the instance is in error, False otherwise
    """
    return cr.status.state is not None and cr.status.state.lower() == "error"


def _get_error_message(cr):
    """
    Get error message from the status of custom resource
    :param cr: Instance to get error message.
    """
    return cr.status.message


def _get_user_pass(client, name):
    # Username
    username = os.environ.get(AZDATA_USERNAME)
    if not username:
        if sys.stdin.isatty():
            username = prompt("Arc SQL managed instance username:")
        else:
            raise ValueError(
                "Please provide an Arc SQL managed instance username "
                "through the env variable AZDATA_USERNAME."
            )
    else:
        client.stdout(
            "Using AZDATA_USERNAME environment variable for `{}` "
            "username.".format(name)
        )

    while username == "sa" or username == "":
        if username == "sa":
            username = prompt(
                "The login 'sa' is not allowed.  Please use a "
                "different login."
            )
        if username == "":
            username = prompt("Login username required. Please enter a login.")

    # Password
    pw = os.environ.get(AZDATA_PASSWORD)
    if not pw:
        if sys.stdin.isatty():
            while not pw:
                pw = prompt_pass("Arc SQL managed instance password:", True)
                if not is_valid_sql_password(pw, "sa"):
                    client.stderr(
                        "\nError: SQL Server passwords must be at "
                        "least 8 characters long, cannot contain the "
                        "username, and must contain characters from "
                        "three of the following four sets: Uppercase "
                        "letters, Lowercase letters, Base 10 digits, "
                        "and Symbols. Please try again.\n"
                    )
                    pw = None
        else:
            raise ValueError(
                "Please provide an Arc SQL managed instance password "
                "through the env variable AZDATA_PASSWORD."
            )
    else:
        client.stdout(
            "Using AZDATA_PASSWORD environment variable for `{}` "
            "password.".format(name)
        )

    return username, pw


def _create_service_certificate(
    client,
    cr,
    name,
    certificate_public_key_file,
    certificate_private_key_file,
    service_certificate_secret,
    is_update = False):
    """
    Creates service certificate based on parameters.
    """
    
    # Handle certificate secret related parameters.
    #
    # Cases:
    #
    # 1. When only one of certificate_public_key_file and certificate_
    #    private_key_file are provided, fail with a message saying both
    #    are required if one is provided.
    #
    # 2. When both certificate_public_key_file and
    #    certificate_private_key_file are provided, then there are
    #    two subcases:
    #
    #    2.1. If service_certificate_secret parameter is NOT provided, use
    #         default name for the secret along with a unique id such as
    #         timestamp appended to it. Check if the secret exists.
    #
    #         2.1.1. If secret does not exist, then create it.
    #
    #         2.1.2. If the secret exists, retry with a different unique
    #                identifier.
    #
    #    2.2. If service_certificate_secret parameter is provided, use that
    #         string as the secret name and check if the secret exists.
    #
    #         2.2.1. If secret does not exist, then create it.
    #
    #         2.2.2. If the secret exists, fail indicating that if the
    #                secret exists and the parameters for certificate files
    #                should not be provided.
    #
    # 3. When both certificate_public_key_file and
    #    certificate_private_key_file are NOT provided, then there are two
    #    subcases:
    #
    #    3.1. If service_certificate_secret parameter is NOT provided, do
    #         NOT use default value. User intends to use system generated
    #         certificate.
    #
    #    3.2. If service_certificate_secret parameter is provided, use that
    #         string as the secret name and check if the secret already
    #         exists.
    #
    #         3.2.1. If the secret exists, validate and use it.
    #
    #         3.2.2. If the secret does not exist, fail.

    create_new_secret = False
    use_existing_secret = False
    default_service_certificate_secret_name = name + "-certificate-secret"

    # Erase the certificate name from the custom resource for not update.
    # It will be added only if necessary upon validation.
    #
    if not is_update:
        cr.spec.security.serviceCertificateSecret = ""

    # Case 1. When only one of certificate_public_key_file and
    #         certificate_private_key_file are provided, fail with a
    #         message saying both are required if one is provided.
    #
    #
    if not certificate_public_key_file and certificate_private_key_file:
        raise ValueError(
            "Certificate public key file path must be provided "
            "when private key path is provided."
        )

    if certificate_public_key_file and not certificate_private_key_file:
        raise ValueError(
            "Certificate private key file path must be provided "
            "when public key path is provided."
        )

    # Case 2. When both certificate_public_key_file and
    #         certificate_private_key_file are provided.
    #
    if certificate_public_key_file and certificate_private_key_file:

        # Case 2.1. If service_certificate_secret parameter is NOT provided,
        #           use default name for the secret along with a unique id
        #           such as timestamp appended to it. Check if the secret
        #           exists.
        #
        if not service_certificate_secret:

            # Case 2.1.1. If secret does not exist, then create it.
            #
            # Case 2.1.2. If the secret exists, retry with a different
            # unique identifier.
            #
            certificate_secret_exists = True
            while certificate_secret_exists:
                timestamp = datetime.now().strftime(
                    "%m-%d-%Y-%H-%M-%S-%f"
                )  # e.g. '07-02-2021-23-00-37-846604'

                # Secret name must be a valid DNS-1123 subdomain name.
                # Kubernetes uses this regex for validation:
                # '[a-z0-9]([-a-z0-9]*[a-z0-9])?
                #  (\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*'
                #
                service_certificate_secret = (
                    default_service_certificate_secret_name
                    + "-"
                    + timestamp
                )

                certificate_secret_exists = (
                    check_secret_exists_with_retries(
                        client.apis.kubernetes,
                        cr.metadata.namespace,
                        service_certificate_secret,
                    )
                )

            # Set flag to create new secret.
            #
            create_new_secret = True

        # Case 2.2. If service_certificate_secret parameter is provided, use
        #           that string asthe secret name and check if the secret
        #           exists.
        #
        else:
            certificate_secret_exists = check_secret_exists_with_retries(
                client.apis.kubernetes, cr.metadata.namespace, service_certificate_secret
            )

            # Case 2.2.1. If secret does not exist, then create it.
            #
            if not certificate_secret_exists:

                # Set flag to create new secret.
                #
                create_new_secret = True

            # Case 2.2.2. If the secret exists, fail indicating that if the
            #             secret exists and the parameters for certificate
            #             files should not be provided.
            #
            else:
                raise ValueError(
                    CERT_ARGUMENT_ERROR_TEMPLATE
                        .format(service_certificate_secret)
                )

    # Case 3. When both certificate_public_key_file and
    #         certificate_private_key_file are NOT provided.
    #
    if not certificate_public_key_file and not certificate_private_key_file:

        # Case 3.1. If service_certificate_secret parameter is NOT provided,
        #           do NOT use default value. User intends to use system
        #           generated certificate.
        #
        if not service_certificate_secret:
            pass

        # Case 3.2. If service_certificate_secret parameter is provided, use
        #           that string as the secret name and check if the secret
        #           already exists.
        #
        else:
            certificate_secret_exists = check_secret_exists_with_retries(
                client.apis.kubernetes,
                cr.metadata.namespace,
                service_certificate_secret
            )

            # Case 3.2.1. If the secret exists, validate and use it.
            #
            if certificate_secret_exists:

                # Set flag to use existing secret.
                #
                use_existing_secret = True

            # Case 3.2.2. If the secret does not exist, fail.
            #
            else:
                raise ValueError(
                    "Kubernetes secret '{0}' does "
                    "not exist. If you intend to use a pre-existing "
                    "secret, please provide correct name of an existing "
                    "secret. If you intend to use a certificate from "
                    "public key and private key files, please provide "
                    "their paths in the parameters --cert-public-key-file "
                    "and --cert-private-key-file.".format(
                        service_certificate_secret
                    )
                )

    # If we decided to create a new secret, create it here.
    #
    if create_new_secret:

        # Validate and parse data from files.
        #
        public_key, private_key = parse_cert_files(
            certificate_public_key_file, certificate_private_key_file
        )

        # Create secret.
        #
        create_certificate_secret(
            client.apis.kubernetes,
            cr.metadata.namespace,
            service_certificate_secret,
            public_key,
            private_key,
        )

        # Set the secret name on custom resource spec to indicate to the
        # operator that we will use certificate from the Kubernetes secret.
        #
        cr.spec.security.serviceCertificateSecret = (
            service_certificate_secret
        )

    # If we decided to use an existing secret, validate it and pass on.
    #
    elif use_existing_secret:

        # Load secret and validate contents.
        #
        validate_certificate_secret(
            client.apis.kubernetes,
            cr.metadata.namespace,
            service_certificate_secret
        )

        # Set the secret name on the custom resource spec to indicate to the
        # operator that a user provided certificate is available to use.
        #
        cr.spec.security.serviceCertificateSecret = (
            service_certificate_secret
        )