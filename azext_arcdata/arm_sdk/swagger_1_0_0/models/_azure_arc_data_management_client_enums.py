# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from enum import Enum, EnumMeta
from six import with_metaclass


class _CaseInsensitiveEnumMeta(EnumMeta):
    def __getitem__(self, name):
        return super().__getitem__(name.upper())

    def __getattr__(cls, name):
        """Return the enum member matching `name`
        We use __getattr__ instead of descriptors or inserting into the enum
        class' __dict__ in order to support `name` and `value` being both
        properties for enum members (which live in the class' __dict__) and
        enum members themselves.
        """
        try:
            return cls._member_map_[name.upper()]
        except KeyError:
            raise AttributeError(name)


class ArcSqlManagedInstanceLicenseType(
    with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)
):
    """The license type to apply for this managed instance."""

    BASE_PRICE = "BasePrice"
    LICENSE_INCLUDED = "LicenseIncluded"


class ArcSqlServerLicenseType(
    with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)
):
    """SQL Server license type."""

    PAID = "Paid"
    FREE = "Free"
    HADR = "HADR"
    UNDEFINED = "Undefined"


class ConnectionStatus(with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)):
    """The cloud connectivity status."""

    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    UNKNOWN = "Unknown"


class DefenderStatus(with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)):
    """Status of Azure Defender."""

    PROTECTED = "Protected"
    UNPROTECTED = "Unprotected"
    UNKNOWN = "Unknown"


class EditionType(with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)):
    """SQL Server edition."""

    EVALUATION = "Evaluation"
    ENTERPRISE = "Enterprise"
    STANDARD = "Standard"
    WEB = "Web"
    DEVELOPER = "Developer"
    EXPRESS = "Express"


class ExtendedLocationTypes(
    with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)
):
    """The type of extendedLocation."""

    CUSTOM_LOCATION = "CustomLocation"


class IdentityType(with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)):
    """The type of identity that creates/modifies resources"""

    USER = "User"
    APPLICATION = "Application"
    MANAGED_IDENTITY = "ManagedIdentity"
    KEY = "Key"


class Infrastructure(with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)):
    """The infrastructure the data controller is running on."""

    AZURE = "azure"
    GCP = "gcp"
    AWS = "aws"
    ALIBABA = "alibaba"
    ONPREMISES = "onpremises"
    OTHER = "other"


class OperationOrigin(with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)):
    """The intended executor of the operation."""

    USER = "user"
    SYSTEM = "system"


class SqlManagedInstanceSkuTier(
    with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)
):
    """The pricing tier for the instance."""

    GENERAL_PURPOSE = "GeneralPurpose"
    BUSINESS_CRITICAL = "BusinessCritical"


class SqlVersion(with_metaclass(_CaseInsensitiveEnumMeta, str, Enum)):
    """SQL Server version."""

    SQL_SERVER2019 = "SQL Server 2019"
    SQL_SERVER2017 = "SQL Server 2017"
    SQL_SERVER2016 = "SQL Server 2016"
