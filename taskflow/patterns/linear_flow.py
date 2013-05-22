# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright (C) 2012 Yahoo! Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from taskflow import exceptions as exc
from taskflow.patterns import ordered_flow


def _convert_to_set(items):
    if not items:
        return set()
    if isinstance(items, set):
        return items
    if isinstance(items, dict):
        return items.keys()
    return set(iter(items))


class Flow(ordered_flow.Flow):
    """A linear chain of tasks that can be applied as one unit or
       rolled back as one unit. Each task in the chain may have requirements
       which are satisfied by the previous task in the chain."""

    def __init__(self, name, tolerant=False, parents=None):
        super(Flow, self).__init__(name, tolerant, parents)
        self._tasks = []

    def _fetch_task_inputs(self, task):
        inputs = {}
        if self.results:
            (_last_task, last_results) = self.results[-1]
            for k in task.requires():
                if last_results and k in last_results:
                    inputs[k] = last_results[k]
        return inputs

    def _validate_provides(self, task):
        requires = _convert_to_set(task.requires())
        last_provides = set()
        last_provider = None
        if self._tasks:
            last_provider = self._tasks[-1]
            last_provides = _convert_to_set(last_provider.provides())
        # Ensure that the last task provides all the needed input for this
        # task to run correctly.
        req_diff = requires.difference(last_provides)
        if req_diff:
            if last_provider is None:
                msg = ("There is no previous task providing the outputs %s"
                       " for %s to correctly execute.") % (req_diff, task)
            else:
                msg = ("%s does not provide the needed outputs %s for %s to"
                       " correctly execute.")
                msg = msg % (last_provider, req_diff, task)
            raise exc.InvalidStateException(msg)

    def add(self, task):
        self._validate_provides(task)
        self._tasks.append(task)

    def order(self):
        return list(self._tasks)
