#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2021, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: bigip_asm_policy_import
short_description: Manage BIG-IP ASM policy imports
description:
   - Manage the policy imports for BIG-IP ASM policies.
version_added: "1.0.0"
options:
  name:
    description:
      - The ASM policy to create or override.
    type: str
    required: True
  policy_type:
    description:
      - The type of the policy to import.
      - When C(policy_type) is C(security), the policy is imported as an application security policy that you can apply
        to a virtual server.
      - When C(policy_type) is C(parent), the policy becomes a parent to which other Security policies attach,
        inheriting its attributes. This policy type cannot be applied to Virtual Servers.
      - This parameter is available on TMOS version 13.x and later and only takes effect when the C(inline) import method
        is used.
    type: str
    default: security
    choices:
      - security
      - parent
  retain_inheritance_settings:
    description:
      - Indicate if an imported security type policy should retain settings when attached to parent policy.
      - This parameter is available on TMOS version 13.x and later and only takes effect when the C(inline) import method
        is used.
    type: bool
  parent_policy:
    description:
      - The parent policy to which the newly imported policy should be attached as child.
      - When C(parent_policy) is specified, the imported C(policy_type) must not be C(parent).
      - This parameter is available on TMOS version 13.x and later and only takes effect when C(inline) import method
        is used.
    type: str
  base64:
    description:
      - Indicates if the imported policy string is encoded in Base64.
      - Parameter only takes effect when using the C(inline) method of import.
    type: bool
  inline:
    description:
      - When specified, the ASM policy is created from a provided string.
      - Content needs to be provided in a valid XML format, otherwise the operation will fail.
    type: str
  encoding:
    description:
      - Specifies the desired application language of the imported policy.
      - The imported policy cannot be a C(parent) type or attached to a C(parent) policy when C(auto-detect)
        encoding is set.
      - When importing a policy to attach to a C(parent) policy, the C(encoding) of the imported policy, if different,
        must be set to be the same value as C(parent_policy), otherwise import will fail.
      - This parameter is available on TMOS version 13.x and later and only takes effect when the C(inline) import method
        is used.
    type: str
    choices:
      - windows-874
      - utf-8
      - koi8-r
      - windows-1253
      - iso-8859-10
      - gbk
      - windows-1256
      - windows-1250
      - iso-8859-13
      - iso-8859-9
      - windows-1251
      - iso-8859-6
      - big5
      - gb2312
      - iso-8859-1
      - windows-1252
      - iso-8859-4
      - iso-8859-2
      - iso-8859-3
      - gb18030
      - shift_jis
      - iso-8859-8
      - euc-kr
      - iso-8859-5
      - iso-8859-7
      - windows-1255
      - euc-jp
      - iso-8859-15
      - windows-1257
      - iso-8859-16
      - auto-detect
  source:
    description:
      - Full path to a policy file to be imported into the BIG-IP ASM.
      - Policy files exported from newer versions of BIG-IP cannot be imported into older
        versions of BIG-IP. The opposite, however, is true; you can import older into
        newer.
      - The file format can be binary or XML.
    type: path
  force:
    description:
      - When set to C(yes) any existing policy with the same name will be overwritten by the new import.
      - Works for both inline and file imports, if the policy does not exist this setting is ignored.
    default: no
    type: bool
  partition:
    description:
      - Device partition on which to create the policy.
      - This parameter is also applied to indicate the partition of the C(parent) policy.
    type: str
    default: Common
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- hosts: all
  collections:
    - f5networks.f5_bigip
  connection: httpapi

  vars:
    ansible_host: "lb.mydomain.com"
    ansible_user: "admin"
    ansible_httpapi_password: "secret"
    ansible_network_os: f5networks.f5_bigip.bigip
    ansible_httpapi_use_ssl: yes

  tasks:
    - name: Import ASM policy
      bigip_asm_policy_import:
        name: new_asm_policy
        file: /root/asm_policy.xml

    - name: Import ASM policy inline
      bigip_asm_policy_import:
        name: foo-policy4
        inline: <xml>content</xml>

    - name: Override existing ASM policy
      bigip_asm_policy_import:
        name: new_asm_policy
        source: /root/asm_policy_new.xml
        force: yes
'''

RETURN = r'''
policy_type:
  description: The type of the policy to import.
  returned: changed
  type: str
  sample: security
retain_inheritance_settings:
  description: Indicate if an imported security type policy should retain settings when attached to the parent policy.
  returned: changed
  type: bool
  sample: yes
parent_policy:
  description: The parent policy to which the newly imported policy should be attached as child.
  returned: changed
  type: str
  sample: /Common/parent
base64:
  description: Indicates if the imported policy string is encoded in Base64.
  returned: changed
  type: bool
  sample: yes
encoding:
  description: The desired application language of the imported policy.
  returned: changed
  type: str
  sample: utf-8
source:
  description: Local path to an ASM policy file.
  returned: changed
  type: str
  sample: /root/some_policy.xml
inline:
  description: Contents of a policy as an inline string.
  returned: changed
  type: str
  sample: <xml>foobar contents</xml>
name:
  description: Name of the ASM policy to be created/overwritten.
  returned: changed
  type: str
  sample: Asm_APP1_Transparent
force:
  description: Set when overwriting an existing policy.
  returned: changed
  type: bool
  sample: yes
'''

import os
import time
from datetime import datetime

from ansible.module_utils.basic import (
    AnsibleModule, env_fallback
)
from ansible.module_utils.connection import Connection

from ..module_utils.common import (
    F5ModuleError, AnsibleF5Parameters, flatten_boolean, fq_name
)
from ..module_utils.client import (
    F5Client, module_provisioned, send_teem
)


class Parameters(AnsibleF5Parameters):
    updatables = []

    returnables = [
        'name',
        'inline',
        'source',
        'force',
        'policy_type',
        'retain_inheritance_settings',
        'parent_policy',
        'base64',
        'encoding',
    ]

    api_attributes = [
        'file',
        'name',
        'policyType',
        'retainInheritanceSettings',
        'parentPolicy',
        'isBase64',
        'applicationLanguage',
    ]

    api_map = {
        'file': 'inline',
        'filename': 'source',
        'policyType': 'policy_type',
        'retainInheritanceSettings': 'retain_inheritance_settings',
        'parentPolicy': 'parent_policy',
        'isBase64': 'base64',
        'applicationLanguage': 'encoding',
    }


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def parent_policy(self):
        if self._values['parent_policy'] is None:
            return None
        if self._values['policy_type'] == 'parent':
            raise F5ModuleError(
                "The 'policy_type' cannot be 'parent' if 'parent_policy' is defined."
            )
        result = dict(fullPath=fq_name(self.partition, self._values['parent_policy']))
        return result

    @property
    def base64(self):
        result = flatten_boolean(self._values['base64'])
        if result == 'yes':
            return True
        if result == 'no':
            return False

    @property
    def retain_inheritance_settings(self):
        result = flatten_boolean(self._values['retain_inheritance_settings'])
        if result == 'yes':
            return True
        if result == 'no':
            return False


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            raise
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    @property
    def parent_policy(self):
        if self._values['parent_policy'] is None:
            return None
        result = self._values['parent_policy']['fullPath']
        return result

    @property
    def retain_inheritance_settings(self):
        result = flatten_boolean(self._values['retain_inheritance_settings'])
        return result

    @property
    def base64(self):
        result = flatten_boolean(self._values['base64'])
        return result


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.connection = kwargs.get('connection', None)
        self.client = F5Client(module=self.module, client=self.connection)
        self.want = ModuleParameters(params=self.module.params)
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def exec_module(self):
        start = datetime.now().isoformat()
        if not module_provisioned(self.client, 'asm'):
            raise F5ModuleError(
                "ASM must be provisioned to use this module."
            )

        result = dict()

        changed = self.policy_import()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        send_teem(self.client, start)
        return result

    def _clear_changes(self):
        redundant = [
            'policy_type',
            'retain_inheritance_settings',
            'parent_policy',
            'base64',
            'encoding',
        ]
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None and key not in redundant:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def policy_import(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        if self.exists():
            if self.want.force is False:
                return False
        if not self.exists() and self.want.force is True:
            self.want.update({'force': None})
        if self.want.inline:
            task = self.inline_import()
            self.wait_for_task(task)
            return True
        self._clear_changes()
        self.import_file_to_device()
        return True

    def exists(self):
        uri = "/mgmt/tm/asm/policies/"
        query = "?$filter=name+eq+{0}+and+partition+eq+{1}&$select=name,partition".format(
            self.want.name, self.want.partition
        )
        response = self.client.get(uri + query)

        if response['code'] not in [200, 201, 202]:
            raise F5ModuleError(response['contents'])

        if 'items' in response['contents'] and response['contents']['items'] != []:
            return True
        return False

    def upload_file_to_device(self, content, name):
        url = "/mgmt/tm/asm/file-transfer/uploads"

        try:
            self.client.plugin.upload_file(url, content, name)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def _get_policy_link(self):
        uri = "/mgmt/tm/asm/policies/"
        query = "?$filter=name+eq+{0}+and+partition+eq+{1}&$select=name,partition".format(
            self.want.name, self.want.partition
        )
        response = self.client.get(uri + query)

        if response['code'] not in [200, 201, 202]:
            raise F5ModuleError(response['contents'])

        policy_link = response['contents']['items'][0]['selfLink']
        return policy_link

    def inline_import(self):
        params = self.changes.api_params()
        params['name'] = fq_name(self.want.partition, self.want.name)

        if self.want.source:
            params['filename'] = os.path.split(self.want.source)[1]
        uri = "/mgmt/tm/asm/tasks/import-policy/"

        if self.want.force:
            params.update(dict(policyReference={'link': self._get_policy_link()}))
            params.pop('name')

        response = self.client.post(uri, data=params)

        if response['code'] not in [200, 201, 202]:
            raise F5ModuleError(response['contents'])

        return response['contents']['id']

    def wait_for_task(self, task_id):
        uri = "/mgmt/tm/asm/tasks/import-policy/{0}".format(task_id)

        while True:
            response = self.client.get(uri)

            if response['code'] not in [200, 201, 202]:
                raise F5ModuleError(response['contents'])

            if response['contents']['status'] in ['COMPLETED', 'FAILURE']:
                break
            time.sleep(1)

        if response['contents']['status'] == 'FAILURE':
            raise F5ModuleError(
                'Failed to import ASM policy.'
            )
        if response['contents']['status'] == 'COMPLETED':
            return True

    def import_file_to_device(self):
        name = os.path.split(self.want.source)[1]
        self.upload_file_to_device(self.want.source, name)
        time.sleep(2)

        task = self.inline_import()
        self.wait_for_task(task)
        return True


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.choices = [
            'windows-874',
            'utf-8',
            'koi8-r',
            'windows-1253',
            'iso-8859-10',
            'gbk',
            'windows-1256',
            'windows-1250',
            'iso-8859-13',
            'iso-8859-9',
            'windows-1251',
            'iso-8859-6',
            'big5',
            'gb2312',
            'iso-8859-1',
            'windows-1252',
            'iso-8859-4',
            'iso-8859-2',
            'iso-8859-3',
            'gb18030',
            'shift_jis',
            'iso-8859-8',
            'euc-kr',
            'iso-8859-5',
            'iso-8859-7',
            'windows-1255',
            'euc-jp',
            'iso-8859-15',
            'windows-1257',
            'iso-8859-16',
            'auto-detect'
        ]
        argument_spec = dict(
            name=dict(
                required=True,
            ),
            source=dict(type='path'),
            inline=dict(),
            policy_type=dict(
                default='security',
                choices=['security', 'parent']
            ),
            retain_inheritance_settings=dict(type='bool'),
            base64=dict(type='bool'),
            parent_policy=dict(),
            encoding=dict(choices=self.choices),
            force=dict(
                type='bool',
                default='no'
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['source', 'inline']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )

    try:
        mm = ModuleManager(module=module, connection=Connection(module._socket_path))
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
