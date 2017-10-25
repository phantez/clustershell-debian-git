#
# Copyright (C) 2007-2015 CEA/DAM
# Copyright (C) 2015-2017 Stephane Thiell <sthiell@stanford.edu>
#
# This file is part of ClusterShell.
#
# ClusterShell is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# ClusterShell is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with ClusterShell; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""
ClusterShell Event handling.

This module contains the base class :class:`.EventHandler` which defines
a simple interface to handle events generated by :class:`.Worker`,
:class:`.EventTimer` and :class:`.EventPort` objects.
"""


class EventHandler(object):
    """ClusterShell EventHandler interface.

    Derived class should implement any of the following methods to listen for
    :class:`.Worker`, :class:`.EventTimer` or :class:`.EventPort` selected
    events. If not implemented, the default behavior is to do nothing.
    """

    def ev_start(self, worker):
        """
        Called to indicate that a worker has just started.

        :param worker: :class:`.Worker` derived object
        """

    def ev_pickup(self, worker, node):
        """
        Called for each node to indicate that a worker command for a
        specific node (or key) has just started.

        .. warning:: The signature of :meth:`EventHandler.ev_pickup` changed
            in ClusterShell 1.8, please update your :class:`.EventHandler`
            derived classes and add the node argument.

        *New in version 1.7.*

        :param worker: :class:`.Worker` derived object
        :param node: node (or key)
        """

    def ev_read(self, worker, node, sname, msg):
        """
        Called to indicate that a worker has data to read from a specific
        node (or key).

        .. warning:: The signature of :meth:`EventHandler.ev_read` changed
            in ClusterShell 1.8, please update your :class:`.EventHandler`
            derived classes and add the node, sname and msg arguments.

        :param worker: :class:`.Worker` derived object
        :param node: node (or key)
        :param sname: stream name
        :param msg: message
        """

    def ev_written(self, worker, node, sname, size):
        """
        Called to indicate that some writing has been done by the worker to a
        node on a given stream. This event is only generated when ``write()``
        is previously called on the worker.

        This handler may be called very often depending on the number of target
        nodes, the amount of data to write and the block size used by the
        worker.

        *New in version 1.7.*

        :param worker: :class:`.Worker` derived object
        :param node: node (or) key
        :param sname: stream name
        :param size: amount of bytes that has just been written to node/stream
            associated with this event
        """

    def ev_hup(self, worker, node, rc):
        """
        Called for each node to indicate that a worker command for a specific
        node has just finished.

        .. warning:: The signature of :meth:`EventHandler.ev_hup` changed
            in ClusterShell 1.8, please update your :class:`.EventHandler`
            derived classes to add the node and rc arguments.

        :param worker: :class:`.Worker` derived object
        :param node: node (or key)
        :param rc: command return code (or None if the worker doesn't support
            command return codes)
        """

    def ev_close(self, worker, timedout):
        """
        Called to indicate that a worker has just finished.

        .. warning:: The signature of :meth:`EventHandler.ev_close` changed
            in ClusterShell 1.8, please update your :class:`.EventHandler`
            derived classes to add the timedout argument. Please use this
            argument instead of the method ``ev_timeout``.

        :param worker: :class:`.Worker` derived object
        :param timedout: boolean set to True if the worker has timed out
        """

    def ev_msg(self, port, msg):
        """
        Called to indicate that a message has been received on an EnginePort.

        Used to deliver messages reliably between tasks.

        :param port: EnginePort object on which a message has been received
        :param msg: the message object received
        """

    def ev_timer(self, timer):
        """
        Called to indicate that a timer is firing.

        :param timer: :class:`.EngineTimer` object that is firing
        """

    def _ev_routing(self, worker, arg):
        """
        Routing event (private). Called to indicate that a (meta)worker has just
        updated one of its route path. You can safely ignore this event.
        """
