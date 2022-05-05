# pylint: disable=too-many-lines
# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator (autorest: 3.8.3, generator: @autorest/python@5.16.0)
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------
from typing import TYPE_CHECKING, cast

from msrest import Serializer

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceExistsError,
    ResourceNotFoundError,
    map_error,
)
from azure.core.paging import ItemPaged
from azure.core.pipeline import PipelineResponse
from azure.core.pipeline.transport import HttpResponse
from azure.core.polling import LROPoller, NoPolling, PollingMethod
from azure.core.polling.base_polling import LROBasePolling
from azure.core.rest import HttpRequest
from azure.core.tracing.decorator import distributed_trace
from ._util import case_insensitive_dict

from .. import models as _models
from .._vendor import _convert_request, _format_url_section

if TYPE_CHECKING:
    # pylint: disable=unused-import,ungrouped-imports
    from typing import Any, Callable, Dict, Iterable, Optional, TypeVar, Union

    T = TypeVar("T")
    ClsType = Optional[
        Callable[
            [PipelineResponse[HttpRequest, HttpResponse], T, Dict[str, Any]],
            Any,
        ]
    ]

_SERIALIZER = Serializer()
_SERIALIZER.client_side_validation = False
# fmt: off

def build_list_request(
    subscription_id,  # type: str
    resource_group_name,  # type: str
    data_controller_name,  # type: str
    **kwargs  # type: Any
):
    # type: (...) -> HttpRequest
    _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
    _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

    api_version = kwargs.pop('api_version', _params.pop('api-version', "2022-03-01-preview"))  # type: str
    accept = _headers.pop('Accept', "application/json")

    # Construct URL
    _url = kwargs.pop("template_url", "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors")  # pylint: disable=line-too-long
    path_format_arguments = {
        "subscriptionId": _SERIALIZER.url("subscription_id", subscription_id, 'str'),
        "resourceGroupName": _SERIALIZER.url("resource_group_name", resource_group_name, 'str'),
        "dataControllerName": _SERIALIZER.url("data_controller_name", data_controller_name, 'str'),
    }

    _url = _format_url_section(_url, **path_format_arguments)

    # Construct parameters
    _params['api-version'] = _SERIALIZER.query("api_version", api_version, 'str')

    # Construct headers
    _headers['Accept'] = _SERIALIZER.header("accept", accept, 'str')

    return HttpRequest(
        method="GET",
        url=_url,
        params=_params,
        headers=_headers,
        **kwargs
    )


def build_create_request_initial(
    subscription_id,  # type: str
    resource_group_name,  # type: str
    data_controller_name,  # type: str
    active_directory_connector_name,  # type: str
    **kwargs  # type: Any
):
    # type: (...) -> HttpRequest
    _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
    _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

    api_version = kwargs.pop('api_version', _params.pop('api-version', "2022-03-01-preview"))  # type: str
    content_type = kwargs.pop('content_type', _headers.pop('Content-Type', None))  # type: Optional[str]
    accept = _headers.pop('Accept', "application/json")

    # Construct URL
    _url = kwargs.pop("template_url", "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}")  # pylint: disable=line-too-long
    path_format_arguments = {
        "subscriptionId": _SERIALIZER.url("subscription_id", subscription_id, 'str'),
        "resourceGroupName": _SERIALIZER.url("resource_group_name", resource_group_name, 'str'),
        "dataControllerName": _SERIALIZER.url("data_controller_name", data_controller_name, 'str'),
        "activeDirectoryConnectorName": _SERIALIZER.url("active_directory_connector_name", active_directory_connector_name, 'str'),
    }

    _url = _format_url_section(_url, **path_format_arguments)

    # Construct parameters
    _params['api-version'] = _SERIALIZER.query("api_version", api_version, 'str')

    # Construct headers
    if content_type is not None:
        _headers['Content-Type'] = _SERIALIZER.header("content_type", content_type, 'str')
    _headers['Accept'] = _SERIALIZER.header("accept", accept, 'str')

    return HttpRequest(
        method="PUT",
        url=_url,
        params=_params,
        headers=_headers,
        **kwargs
    )


def build_delete_request_initial(
    subscription_id,  # type: str
    resource_group_name,  # type: str
    data_controller_name,  # type: str
    active_directory_connector_name,  # type: str
    **kwargs  # type: Any
):
    # type: (...) -> HttpRequest
    _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
    _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

    api_version = kwargs.pop('api_version', _params.pop('api-version', "2022-03-01-preview"))  # type: str
    accept = _headers.pop('Accept', "application/json")

    # Construct URL
    _url = kwargs.pop("template_url", "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}")  # pylint: disable=line-too-long
    path_format_arguments = {
        "subscriptionId": _SERIALIZER.url("subscription_id", subscription_id, 'str'),
        "resourceGroupName": _SERIALIZER.url("resource_group_name", resource_group_name, 'str'),
        "dataControllerName": _SERIALIZER.url("data_controller_name", data_controller_name, 'str'),
        "activeDirectoryConnectorName": _SERIALIZER.url("active_directory_connector_name", active_directory_connector_name, 'str'),
    }

    _url = _format_url_section(_url, **path_format_arguments)

    # Construct parameters
    _params['api-version'] = _SERIALIZER.query("api_version", api_version, 'str')

    # Construct headers
    _headers['Accept'] = _SERIALIZER.header("accept", accept, 'str')

    return HttpRequest(
        method="DELETE",
        url=_url,
        params=_params,
        headers=_headers,
        **kwargs
    )


def build_get_request(
    subscription_id,  # type: str
    resource_group_name,  # type: str
    data_controller_name,  # type: str
    active_directory_connector_name,  # type: str
    **kwargs  # type: Any
):
    # type: (...) -> HttpRequest
    _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
    _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

    api_version = kwargs.pop('api_version', _params.pop('api-version', "2022-03-01-preview"))  # type: str
    accept = _headers.pop('Accept', "application/json")

    # Construct URL
    _url = kwargs.pop("template_url", "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}")  # pylint: disable=line-too-long
    path_format_arguments = {
        "subscriptionId": _SERIALIZER.url("subscription_id", subscription_id, 'str'),
        "resourceGroupName": _SERIALIZER.url("resource_group_name", resource_group_name, 'str'),
        "dataControllerName": _SERIALIZER.url("data_controller_name", data_controller_name, 'str'),
        "activeDirectoryConnectorName": _SERIALIZER.url("active_directory_connector_name", active_directory_connector_name, 'str'),
    }

    _url = _format_url_section(_url, **path_format_arguments)

    # Construct parameters
    _params['api-version'] = _SERIALIZER.query("api_version", api_version, 'str')

    # Construct headers
    _headers['Accept'] = _SERIALIZER.header("accept", accept, 'str')

    return HttpRequest(
        method="GET",
        url=_url,
        params=_params,
        headers=_headers,
        **kwargs
    )

# fmt: on
class ActiveDirectoryConnectorsOperations(object):
    """
    .. warning::
        **DO NOT** instantiate this class directly.

        Instead, you should access the following operations through
        :class:`~azure_arc_data_management_client.AzureArcDataManagementClient`'s
        :attr:`active_directory_connectors` attribute.
    """

    models = _models

    def __init__(self, *args, **kwargs):
        input_args = list(args)
        self._client = input_args.pop(0) if input_args else kwargs.pop("client")
        self._config = input_args.pop(0) if input_args else kwargs.pop("config")
        self._serialize = (
            input_args.pop(0) if input_args else kwargs.pop("serializer")
        )
        self._deserialize = (
            input_args.pop(0) if input_args else kwargs.pop("deserializer")
        )

    @distributed_trace
    def list(
        self,
        resource_group_name,  # type: str
        data_controller_name,  # type: str
        **kwargs,  # type: Any
    ):
        # type: (...) -> Iterable[_models.ActiveDirectoryConnectorListResult]
        """List the active directory connectors associated with the given data controller.

        List the active directory connectors associated with the given data controller.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param data_controller_name: The name of the data controller.
        :type data_controller_name: str
        :keyword callable cls: A custom type or function that will be passed the direct response
        :return: An iterator like instance of either ActiveDirectoryConnectorListResult or the result
         of cls(response)
        :rtype:
         ~azure.core.paging.ItemPaged[~azure_arc_data_management_client.models.ActiveDirectoryConnectorListResult]
        :raises: ~azure.core.exceptions.HttpResponseError
        """
        _headers = kwargs.pop("headers", {}) or {}
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        cls = kwargs.pop(
            "cls", None
        )  # type: ClsType[_models.ActiveDirectoryConnectorListResult]

        error_map = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
        }
        error_map.update(kwargs.pop("error_map", {}) or {})

        def prepare_request(next_link=None):
            if not next_link:

                request = build_list_request(
                    subscription_id=self._config.subscription_id,
                    resource_group_name=resource_group_name,
                    data_controller_name=data_controller_name,
                    api_version=api_version,
                    template_url=self.list.metadata["url"],
                    headers=_headers,
                    params=_params,
                )
                request = _convert_request(request)
                request.url = self._client.format_url(request.url)  # type: ignore

            else:

                request = build_list_request(
                    subscription_id=self._config.subscription_id,
                    resource_group_name=resource_group_name,
                    data_controller_name=data_controller_name,
                    api_version=api_version,
                    template_url=next_link,
                    headers=_headers,
                    params=_params,
                )
                request = _convert_request(request)
                request.url = self._client.format_url(request.url)  # type: ignore
                request.method = "GET"
            return request

        def extract_data(pipeline_response):
            deserialized = self._deserialize(
                "ActiveDirectoryConnectorListResult", pipeline_response
            )
            list_of_elem = deserialized.value
            if cls:
                list_of_elem = cls(list_of_elem)
            return deserialized.next_link or None, iter(list_of_elem)

        def get_next(next_link=None):
            request = prepare_request(next_link)

            pipeline_response = (
                self._client._pipeline.run(  # pylint: disable=protected-access
                    request, stream=False, **kwargs
                )
            )
            response = pipeline_response.http_response

            if response.status_code not in [200]:
                map_error(
                    status_code=response.status_code,
                    response=response,
                    error_map=error_map,
                )
                error = self._deserialize.failsafe_deserialize(
                    _models.ErrorResponse, pipeline_response
                )
                raise HttpResponseError(response=response, model=error)

            return pipeline_response

        return ItemPaged(get_next, extract_data)

    list.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors"}  # type: ignore

    def _create_initial(
        self,
        resource_group_name,  # type: str
        data_controller_name,  # type: str
        active_directory_connector_name,  # type: str
        active_directory_connector_resource,  # type: _models.ActiveDirectoryConnectorResource
        **kwargs,  # type: Any
    ):
        # type: (...) -> _models.ActiveDirectoryConnectorResource
        error_map = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
        }
        error_map.update(kwargs.pop("error_map", {}) or {})

        _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        content_type = kwargs.pop(
            "content_type", _headers.pop("Content-Type", "application/json")
        )  # type: Optional[str]
        cls = kwargs.pop(
            "cls", None
        )  # type: ClsType[_models.ActiveDirectoryConnectorResource]

        _json = self._serialize.body(
            active_directory_connector_resource,
            "ActiveDirectoryConnectorResource",
        )

        request = build_create_request_initial(
            subscription_id=self._config.subscription_id,
            resource_group_name=resource_group_name,
            data_controller_name=data_controller_name,
            active_directory_connector_name=active_directory_connector_name,
            api_version=api_version,
            content_type=content_type,
            json=_json,
            template_url=self._create_initial.metadata["url"],
            headers=_headers,
            params=_params,
        )
        request = _convert_request(request)
        request.url = self._client.format_url(request.url)  # type: ignore

        pipeline_response = self._client._pipeline.run(  # type: ignore # pylint: disable=protected-access
            request, stream=False, **kwargs
        )
        response = pipeline_response.http_response

        if response.status_code not in [200, 201]:
            map_error(
                status_code=response.status_code,
                response=response,
                error_map=error_map,
            )
            raise HttpResponseError(response=response)

        if response.status_code == 200:
            deserialized = self._deserialize(
                "ActiveDirectoryConnectorResource", pipeline_response
            )

        if response.status_code == 201:
            deserialized = self._deserialize(
                "ActiveDirectoryConnectorResource", pipeline_response
            )

        if cls:
            return cls(pipeline_response, deserialized, {})

        return deserialized

    _create_initial.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}"}  # type: ignore

    @distributed_trace
    def begin_create(
        self,
        resource_group_name,  # type: str
        data_controller_name,  # type: str
        active_directory_connector_name,  # type: str
        active_directory_connector_resource,  # type: _models.ActiveDirectoryConnectorResource
        **kwargs,  # type: Any
    ):
        # type: (...) -> LROPoller[_models.ActiveDirectoryConnectorResource]
        """Creates or replaces an Active Directory connector resource.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param data_controller_name: The name of the data controller.
        :type data_controller_name: str
        :param active_directory_connector_name: The name of the Active Directory connector instance.
        :type active_directory_connector_name: str
        :param active_directory_connector_resource: desc.
        :type active_directory_connector_resource:
         ~azure_arc_data_management_client.models.ActiveDirectoryConnectorResource
        :keyword callable cls: A custom type or function that will be passed the direct response
        :keyword str continuation_token: A continuation token to restart a poller from a saved state.
        :keyword polling: By default, your polling method will be LROBasePolling. Pass in False for
         this operation to not poll, or pass in your own initialized polling object for a personal
         polling strategy.
        :paramtype polling: bool or ~azure.core.polling.PollingMethod
        :keyword int polling_interval: Default waiting time between two polls for LRO operations if no
         Retry-After header is present.
        :return: An instance of LROPoller that returns either ActiveDirectoryConnectorResource or the
         result of cls(response)
        :rtype:
         ~azure.core.polling.LROPoller[~azure_arc_data_management_client.models.ActiveDirectoryConnectorResource]
        :raises: ~azure.core.exceptions.HttpResponseError
        """
        _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        content_type = kwargs.pop(
            "content_type", _headers.pop("Content-Type", "application/json")
        )  # type: Optional[str]
        cls = kwargs.pop(
            "cls", None
        )  # type: ClsType[_models.ActiveDirectoryConnectorResource]
        polling = kwargs.pop(
            "polling", True
        )  # type: Union[bool, PollingMethod]
        lro_delay = kwargs.pop(
            "polling_interval", self._config.polling_interval
        )
        cont_token = kwargs.pop(
            "continuation_token", None
        )  # type: Optional[str]
        if cont_token is None:
            raw_result = self._create_initial(  # type: ignore
                resource_group_name=resource_group_name,
                data_controller_name=data_controller_name,
                active_directory_connector_name=active_directory_connector_name,
                active_directory_connector_resource=active_directory_connector_resource,
                api_version=api_version,
                content_type=content_type,
                cls=lambda x, y, z: x,
                headers=_headers,
                params=_params,
                **kwargs,
            )
        kwargs.pop("error_map", None)

        def get_long_running_output(pipeline_response):
            deserialized = self._deserialize(
                "ActiveDirectoryConnectorResource", pipeline_response
            )
            if cls:
                return cls(pipeline_response, deserialized, {})
            return deserialized

        if polling is True:
            polling_method = cast(
                PollingMethod,
                LROBasePolling(
                    lro_delay,
                    lro_options={"final-state-via": "azure-async-operation"},
                    **kwargs,
                ),
            )  # type: PollingMethod
        elif polling is False:
            polling_method = cast(PollingMethod, NoPolling())
        else:
            polling_method = polling
        if cont_token:
            return LROPoller.from_continuation_token(
                polling_method=polling_method,
                continuation_token=cont_token,
                client=self._client,
                deserialization_callback=get_long_running_output,
            )
        return LROPoller(
            self._client, raw_result, get_long_running_output, polling_method
        )

    begin_create.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}"}  # type: ignore

    def _delete_initial(  # pylint: disable=inconsistent-return-statements
        self,
        resource_group_name,  # type: str
        data_controller_name,  # type: str
        active_directory_connector_name,  # type: str
        **kwargs,  # type: Any
    ):
        # type: (...) -> None
        error_map = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
        }
        error_map.update(kwargs.pop("error_map", {}) or {})

        _headers = kwargs.pop("headers", {}) or {}
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        cls = kwargs.pop("cls", None)  # type: ClsType[None]

        request = build_delete_request_initial(
            subscription_id=self._config.subscription_id,
            resource_group_name=resource_group_name,
            data_controller_name=data_controller_name,
            active_directory_connector_name=active_directory_connector_name,
            api_version=api_version,
            template_url=self._delete_initial.metadata["url"],
            headers=_headers,
            params=_params,
        )
        request = _convert_request(request)
        request.url = self._client.format_url(request.url)  # type: ignore

        pipeline_response = self._client._pipeline.run(  # type: ignore # pylint: disable=protected-access
            request, stream=False, **kwargs
        )
        response = pipeline_response.http_response

        if response.status_code not in [200, 202, 204]:
            map_error(
                status_code=response.status_code,
                response=response,
                error_map=error_map,
            )
            raise HttpResponseError(response=response)

        if cls:
            return cls(pipeline_response, None, {})

    _delete_initial.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}"}  # type: ignore

    @distributed_trace
    def begin_delete(  # pylint: disable=inconsistent-return-statements
        self,
        resource_group_name,  # type: str
        data_controller_name,  # type: str
        active_directory_connector_name,  # type: str
        **kwargs,  # type: Any
    ):
        # type: (...) -> LROPoller[None]
        """Deletes an Active Directory connector resource.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param data_controller_name: The name of the data controller.
        :type data_controller_name: str
        :param active_directory_connector_name: The name of the Active Directory connector instance.
        :type active_directory_connector_name: str
        :keyword callable cls: A custom type or function that will be passed the direct response
        :keyword str continuation_token: A continuation token to restart a poller from a saved state.
        :keyword polling: By default, your polling method will be LROBasePolling. Pass in False for
         this operation to not poll, or pass in your own initialized polling object for a personal
         polling strategy.
        :paramtype polling: bool or ~azure.core.polling.PollingMethod
        :keyword int polling_interval: Default waiting time between two polls for LRO operations if no
         Retry-After header is present.
        :return: An instance of LROPoller that returns either None or the result of cls(response)
        :rtype: ~azure.core.polling.LROPoller[None]
        :raises: ~azure.core.exceptions.HttpResponseError
        """
        _headers = kwargs.pop("headers", {}) or {}
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        cls = kwargs.pop("cls", None)  # type: ClsType[None]
        polling = kwargs.pop(
            "polling", True
        )  # type: Union[bool, PollingMethod]
        lro_delay = kwargs.pop(
            "polling_interval", self._config.polling_interval
        )
        cont_token = kwargs.pop(
            "continuation_token", None
        )  # type: Optional[str]
        if cont_token is None:
            raw_result = self._delete_initial(  # type: ignore
                resource_group_name=resource_group_name,
                data_controller_name=data_controller_name,
                active_directory_connector_name=active_directory_connector_name,
                api_version=api_version,
                cls=lambda x, y, z: x,
                headers=_headers,
                params=_params,
                **kwargs,
            )
        kwargs.pop("error_map", None)

        def get_long_running_output(pipeline_response):
            if cls:
                return cls(pipeline_response, None, {})

        if polling is True:
            polling_method = cast(
                PollingMethod, LROBasePolling(lro_delay, **kwargs)
            )  # type: PollingMethod
        elif polling is False:
            polling_method = cast(PollingMethod, NoPolling())
        else:
            polling_method = polling
        if cont_token:
            return LROPoller.from_continuation_token(
                polling_method=polling_method,
                continuation_token=cont_token,
                client=self._client,
                deserialization_callback=get_long_running_output,
            )
        return LROPoller(
            self._client, raw_result, get_long_running_output, polling_method
        )

    begin_delete.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}"}  # type: ignore

    @distributed_trace
    def get(
        self,
        resource_group_name,  # type: str
        data_controller_name,  # type: str
        active_directory_connector_name,  # type: str
        **kwargs,  # type: Any
    ):
        # type: (...) -> _models.ActiveDirectoryConnectorResource
        """Retrieves an Active Directory connector resource.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param data_controller_name: The name of the data controller.
        :type data_controller_name: str
        :param active_directory_connector_name: The name of the Active Directory connector instance.
        :type active_directory_connector_name: str
        :keyword callable cls: A custom type or function that will be passed the direct response
        :return: ActiveDirectoryConnectorResource, or the result of cls(response)
        :rtype: ~azure_arc_data_management_client.models.ActiveDirectoryConnectorResource
        :raises: ~azure.core.exceptions.HttpResponseError
        """
        error_map = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
        }
        error_map.update(kwargs.pop("error_map", {}) or {})

        _headers = kwargs.pop("headers", {}) or {}
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        cls = kwargs.pop(
            "cls", None
        )  # type: ClsType[_models.ActiveDirectoryConnectorResource]

        request = build_get_request(
            subscription_id=self._config.subscription_id,
            resource_group_name=resource_group_name,
            data_controller_name=data_controller_name,
            active_directory_connector_name=active_directory_connector_name,
            api_version=api_version,
            template_url=self.get.metadata["url"],
            headers=_headers,
            params=_params,
        )
        request = _convert_request(request)
        request.url = self._client.format_url(request.url)  # type: ignore

        pipeline_response = self._client._pipeline.run(  # type: ignore # pylint: disable=protected-access
            request, stream=False, **kwargs
        )
        response = pipeline_response.http_response

        if response.status_code not in [200]:
            map_error(
                status_code=response.status_code,
                response=response,
                error_map=error_map,
            )
            error = self._deserialize.failsafe_deserialize(
                _models.ErrorResponse, pipeline_response
            )
            raise HttpResponseError(response=response, model=error)

        deserialized = self._deserialize(
            "ActiveDirectoryConnectorResource", pipeline_response
        )

        if cls:
            return cls(pipeline_response, deserialized, {})

        return deserialized

    get.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/dataControllers/{dataControllerName}/activeDirectoryConnectors/{activeDirectoryConnectorName}"}  # type: ignore
