# pylint: disable=too-many-lines
# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator (autorest: 3.8.3, generator: @autorest/python@5.16.0)
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------
from typing import (
    Any,
    AsyncIterable,
    Callable,
    Dict,
    Optional,
    TypeVar,
    Union,
    cast,
)

from azure.core.async_paging import AsyncItemPaged, AsyncList
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceExistsError,
    ResourceNotFoundError,
    map_error,
)
from azure.core.pipeline import PipelineResponse
from azure.core.pipeline.transport import AsyncHttpResponse
from azure.core.polling import (
    AsyncLROPoller,
    AsyncNoPolling,
    AsyncPollingMethod,
)
from azure.core.polling.async_base_polling import AsyncLROBasePolling
from azure.core.rest import HttpRequest
from azure.core.tracing.decorator import distributed_trace
from azure.core.tracing.decorator_async import distributed_trace_async
from ...operations._util import case_insensitive_dict

from ... import models as _models
from ..._vendor import _convert_request
from ...operations._sql_server_instances_operations import (
    build_create_request_initial,
    build_delete_request_initial,
    build_get_request,
    build_list_by_resource_group_request,
    build_list_request,
    build_update_request,
)

T = TypeVar("T")
ClsType = Optional[
    Callable[
        [PipelineResponse[HttpRequest, AsyncHttpResponse], T, Dict[str, Any]],
        Any,
    ]
]


class SqlServerInstancesOperations:
    """
    .. warning::
        **DO NOT** instantiate this class directly.

        Instead, you should access the following operations through
        :class:`~azure_arc_data_management_client.aio.AzureArcDataManagementClient`'s
        :attr:`sql_server_instances` attribute.
    """

    models = _models

    def __init__(self, *args, **kwargs) -> None:
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
        self, **kwargs: Any
    ) -> AsyncIterable[_models.SqlServerInstanceListResult]:
        """List sqlServerInstance resources in the subscription.

        List sqlServerInstance resources in the subscription.

        :keyword callable cls: A custom type or function that will be passed the direct response
        :return: An iterator like instance of either SqlServerInstanceListResult or the result of
         cls(response)
        :rtype:
         ~azure.core.async_paging.AsyncItemPaged[~azure_arc_data_management_client.models.SqlServerInstanceListResult]
        :raises: ~azure.core.exceptions.HttpResponseError
        """
        _headers = kwargs.pop("headers", {}) or {}
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        cls = kwargs.pop(
            "cls", None
        )  # type: ClsType[_models.SqlServerInstanceListResult]

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
                    api_version=api_version,
                    template_url=next_link,
                    headers=_headers,
                    params=_params,
                )
                request = _convert_request(request)
                request.url = self._client.format_url(request.url)  # type: ignore
                request.method = "GET"
            return request

        async def extract_data(pipeline_response):
            deserialized = self._deserialize(
                "SqlServerInstanceListResult", pipeline_response
            )
            list_of_elem = deserialized.value
            if cls:
                list_of_elem = cls(list_of_elem)
            return deserialized.next_link or None, AsyncList(list_of_elem)

        async def get_next(next_link=None):
            request = prepare_request(next_link)

            pipeline_response = await self._client._pipeline.run(  # pylint: disable=protected-access
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

            return pipeline_response

        return AsyncItemPaged(get_next, extract_data)

    list.metadata = {"url": "/subscriptions/{subscriptionId}/providers/Microsoft.AzureArcData/sqlServerInstances"}  # type: ignore

    @distributed_trace
    def list_by_resource_group(
        self, resource_group_name: str, **kwargs: Any
    ) -> AsyncIterable[_models.SqlServerInstanceListResult]:
        """List sqlServerInstance resources in the resource group.

        Gets all sqlServerInstances in a resource group.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :keyword callable cls: A custom type or function that will be passed the direct response
        :return: An iterator like instance of either SqlServerInstanceListResult or the result of
         cls(response)
        :rtype:
         ~azure.core.async_paging.AsyncItemPaged[~azure_arc_data_management_client.models.SqlServerInstanceListResult]
        :raises: ~azure.core.exceptions.HttpResponseError
        """
        _headers = kwargs.pop("headers", {}) or {}
        _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

        api_version = kwargs.pop(
            "api_version", _params.pop("api-version", "2022-03-01-preview")
        )  # type: str
        cls = kwargs.pop(
            "cls", None
        )  # type: ClsType[_models.SqlServerInstanceListResult]

        error_map = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
        }
        error_map.update(kwargs.pop("error_map", {}) or {})

        def prepare_request(next_link=None):
            if not next_link:

                request = build_list_by_resource_group_request(
                    subscription_id=self._config.subscription_id,
                    resource_group_name=resource_group_name,
                    api_version=api_version,
                    template_url=self.list_by_resource_group.metadata["url"],
                    headers=_headers,
                    params=_params,
                )
                request = _convert_request(request)
                request.url = self._client.format_url(request.url)  # type: ignore

            else:

                request = build_list_by_resource_group_request(
                    subscription_id=self._config.subscription_id,
                    resource_group_name=resource_group_name,
                    api_version=api_version,
                    template_url=next_link,
                    headers=_headers,
                    params=_params,
                )
                request = _convert_request(request)
                request.url = self._client.format_url(request.url)  # type: ignore
                request.method = "GET"
            return request

        async def extract_data(pipeline_response):
            deserialized = self._deserialize(
                "SqlServerInstanceListResult", pipeline_response
            )
            list_of_elem = deserialized.value
            if cls:
                list_of_elem = cls(list_of_elem)
            return deserialized.next_link or None, AsyncList(list_of_elem)

        async def get_next(next_link=None):
            request = prepare_request(next_link)

            pipeline_response = await self._client._pipeline.run(  # pylint: disable=protected-access
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

            return pipeline_response

        return AsyncItemPaged(get_next, extract_data)

    list_by_resource_group.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/sqlServerInstances"}  # type: ignore

    @distributed_trace_async
    async def get(
        self,
        resource_group_name: str,
        sql_server_instance_name: str,
        **kwargs: Any,
    ) -> _models.SqlServerInstance:
        """Retrieves a SQL Server Instance resource.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param sql_server_instance_name: Name of SQL Server Instance.
        :type sql_server_instance_name: str
        :keyword callable cls: A custom type or function that will be passed the direct response
        :return: SqlServerInstance, or the result of cls(response)
        :rtype: ~azure_arc_data_management_client.models.SqlServerInstance
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
        )  # type: ClsType[_models.SqlServerInstance]

        request = build_get_request(
            subscription_id=self._config.subscription_id,
            resource_group_name=resource_group_name,
            sql_server_instance_name=sql_server_instance_name,
            api_version=api_version,
            template_url=self.get.metadata["url"],
            headers=_headers,
            params=_params,
        )
        request = _convert_request(request)
        request.url = self._client.format_url(request.url)  # type: ignore

        pipeline_response = await self._client._pipeline.run(  # type: ignore # pylint: disable=protected-access
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

        deserialized = self._deserialize("SqlServerInstance", pipeline_response)

        if cls:
            return cls(pipeline_response, deserialized, {})

        return deserialized

    get.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/sqlServerInstances/{sqlServerInstanceName}"}  # type: ignore

    async def _create_initial(
        self,
        resource_group_name: str,
        sql_server_instance_name: str,
        sql_server_instance: _models.SqlServerInstance,
        **kwargs: Any,
    ) -> _models.SqlServerInstance:
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
        )  # type: ClsType[_models.SqlServerInstance]

        _json = self._serialize.body(sql_server_instance, "SqlServerInstance")

        request = build_create_request_initial(
            subscription_id=self._config.subscription_id,
            resource_group_name=resource_group_name,
            sql_server_instance_name=sql_server_instance_name,
            api_version=api_version,
            content_type=content_type,
            json=_json,
            template_url=self._create_initial.metadata["url"],
            headers=_headers,
            params=_params,
        )
        request = _convert_request(request)
        request.url = self._client.format_url(request.url)  # type: ignore

        pipeline_response = await self._client._pipeline.run(  # type: ignore # pylint: disable=protected-access
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
                "SqlServerInstance", pipeline_response
            )

        if response.status_code == 201:
            deserialized = self._deserialize(
                "SqlServerInstance", pipeline_response
            )

        if cls:
            return cls(pipeline_response, deserialized, {})

        return deserialized

    _create_initial.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/sqlServerInstances/{sqlServerInstanceName}"}  # type: ignore

    @distributed_trace_async
    async def begin_create(
        self,
        resource_group_name: str,
        sql_server_instance_name: str,
        sql_server_instance: _models.SqlServerInstance,
        **kwargs: Any,
    ) -> AsyncLROPoller[_models.SqlServerInstance]:
        """Creates or replaces a SQL Server Instance resource.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param sql_server_instance_name: Name of SQL Server Instance.
        :type sql_server_instance_name: str
        :param sql_server_instance: The SQL Server Instance to be created or updated.
        :type sql_server_instance: ~azure_arc_data_management_client.models.SqlServerInstance
        :keyword callable cls: A custom type or function that will be passed the direct response
        :keyword str continuation_token: A continuation token to restart a poller from a saved state.
        :keyword polling: By default, your polling method will be AsyncLROBasePolling. Pass in False
         for this operation to not poll, or pass in your own initialized polling object for a personal
         polling strategy.
        :paramtype polling: bool or ~azure.core.polling.AsyncPollingMethod
        :keyword int polling_interval: Default waiting time between two polls for LRO operations if no
         Retry-After header is present.
        :return: An instance of AsyncLROPoller that returns either SqlServerInstance or the result of
         cls(response)
        :rtype:
         ~azure.core.polling.AsyncLROPoller[~azure_arc_data_management_client.models.SqlServerInstance]
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
        )  # type: ClsType[_models.SqlServerInstance]
        polling = kwargs.pop(
            "polling", True
        )  # type: Union[bool, AsyncPollingMethod]
        lro_delay = kwargs.pop(
            "polling_interval", self._config.polling_interval
        )
        cont_token = kwargs.pop(
            "continuation_token", None
        )  # type: Optional[str]
        if cont_token is None:
            raw_result = await self._create_initial(  # type: ignore
                resource_group_name=resource_group_name,
                sql_server_instance_name=sql_server_instance_name,
                sql_server_instance=sql_server_instance,
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
                "SqlServerInstance", pipeline_response
            )
            if cls:
                return cls(pipeline_response, deserialized, {})
            return deserialized

        if polling is True:
            polling_method = cast(
                AsyncPollingMethod,
                AsyncLROBasePolling(
                    lro_delay,
                    lro_options={"final-state-via": "azure-async-operation"},
                    **kwargs,
                ),
            )  # type: AsyncPollingMethod
        elif polling is False:
            polling_method = cast(AsyncPollingMethod, AsyncNoPolling())
        else:
            polling_method = polling
        if cont_token:
            return AsyncLROPoller.from_continuation_token(
                polling_method=polling_method,
                continuation_token=cont_token,
                client=self._client,
                deserialization_callback=get_long_running_output,
            )
        return AsyncLROPoller(
            self._client, raw_result, get_long_running_output, polling_method
        )

    begin_create.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/sqlServerInstances/{sqlServerInstanceName}"}  # type: ignore

    async def _delete_initial(  # pylint: disable=inconsistent-return-statements
        self,
        resource_group_name: str,
        sql_server_instance_name: str,
        **kwargs: Any,
    ) -> None:
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
            sql_server_instance_name=sql_server_instance_name,
            api_version=api_version,
            template_url=self._delete_initial.metadata["url"],
            headers=_headers,
            params=_params,
        )
        request = _convert_request(request)
        request.url = self._client.format_url(request.url)  # type: ignore

        pipeline_response = await self._client._pipeline.run(  # type: ignore # pylint: disable=protected-access
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

    _delete_initial.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/sqlServerInstances/{sqlServerInstanceName}"}  # type: ignore

    @distributed_trace_async
    async def begin_delete(  # pylint: disable=inconsistent-return-statements
        self,
        resource_group_name: str,
        sql_server_instance_name: str,
        **kwargs: Any,
    ) -> AsyncLROPoller[None]:
        """Deletes a SQL Server Instance resource.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param sql_server_instance_name: Name of SQL Server Instance.
        :type sql_server_instance_name: str
        :keyword callable cls: A custom type or function that will be passed the direct response
        :keyword str continuation_token: A continuation token to restart a poller from a saved state.
        :keyword polling: By default, your polling method will be AsyncLROBasePolling. Pass in False
         for this operation to not poll, or pass in your own initialized polling object for a personal
         polling strategy.
        :paramtype polling: bool or ~azure.core.polling.AsyncPollingMethod
        :keyword int polling_interval: Default waiting time between two polls for LRO operations if no
         Retry-After header is present.
        :return: An instance of AsyncLROPoller that returns either None or the result of cls(response)
        :rtype: ~azure.core.polling.AsyncLROPoller[None]
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
        )  # type: Union[bool, AsyncPollingMethod]
        lro_delay = kwargs.pop(
            "polling_interval", self._config.polling_interval
        )
        cont_token = kwargs.pop(
            "continuation_token", None
        )  # type: Optional[str]
        if cont_token is None:
            raw_result = await self._delete_initial(  # type: ignore
                resource_group_name=resource_group_name,
                sql_server_instance_name=sql_server_instance_name,
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
                AsyncPollingMethod, AsyncLROBasePolling(lro_delay, **kwargs)
            )  # type: AsyncPollingMethod
        elif polling is False:
            polling_method = cast(AsyncPollingMethod, AsyncNoPolling())
        else:
            polling_method = polling
        if cont_token:
            return AsyncLROPoller.from_continuation_token(
                polling_method=polling_method,
                continuation_token=cont_token,
                client=self._client,
                deserialization_callback=get_long_running_output,
            )
        return AsyncLROPoller(
            self._client, raw_result, get_long_running_output, polling_method
        )

    begin_delete.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/sqlServerInstances/{sqlServerInstanceName}"}  # type: ignore

    @distributed_trace_async
    async def update(
        self,
        resource_group_name: str,
        sql_server_instance_name: str,
        parameters: _models.SqlServerInstanceUpdate,
        **kwargs: Any,
    ) -> _models.SqlServerInstance:
        """Updates a SQL Server Instance resource.

        :param resource_group_name: The name of the Azure resource group.
        :type resource_group_name: str
        :param sql_server_instance_name: Name of SQL Server Instance.
        :type sql_server_instance_name: str
        :param parameters: The SQL Server Instance.
        :type parameters: ~azure_arc_data_management_client.models.SqlServerInstanceUpdate
        :keyword callable cls: A custom type or function that will be passed the direct response
        :return: SqlServerInstance, or the result of cls(response)
        :rtype: ~azure_arc_data_management_client.models.SqlServerInstance
        :raises: ~azure.core.exceptions.HttpResponseError
        """
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
        )  # type: ClsType[_models.SqlServerInstance]

        _json = self._serialize.body(parameters, "SqlServerInstanceUpdate")

        request = build_update_request(
            subscription_id=self._config.subscription_id,
            resource_group_name=resource_group_name,
            sql_server_instance_name=sql_server_instance_name,
            api_version=api_version,
            content_type=content_type,
            json=_json,
            template_url=self.update.metadata["url"],
            headers=_headers,
            params=_params,
        )
        request = _convert_request(request)
        request.url = self._client.format_url(request.url)  # type: ignore

        pipeline_response = await self._client._pipeline.run(  # type: ignore # pylint: disable=protected-access
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

        deserialized = self._deserialize("SqlServerInstance", pipeline_response)

        if cls:
            return cls(pipeline_response, deserialized, {})

        return deserialized

    update.metadata = {"url": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.AzureArcData/sqlServerInstances/{sqlServerInstanceName}"}  # type: ignore
