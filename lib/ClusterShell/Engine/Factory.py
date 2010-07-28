#
# Copyright CEA/DAM/DIF (2009, 2010)
#  Contributor: Stephane THIELL <stephane.thiell@cea.fr>
#
# This file is part of the ClusterShell library.
#
# This software is governed by the CeCILL-C license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL-C
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-C license and that you accept its terms.
#
# $Id: Factory.py 238 2010-02-25 22:30:31Z st-cea $

"""
Engine Factory to select the best working event engine for the current
version of Python and Operating System.
"""

import sys

from ClusterShell.Engine.Engine import EngineNotSupportedError

# Available event engines
from ClusterShell.Engine.EPoll import EngineEPoll
from ClusterShell.Engine.Poll import EnginePoll


class PreferredEngine(object):
    """
    Preferred Engine selection metaclass (DP Abstract Factory).
    """

    engines = { EngineEPoll.identifier: EngineEPoll,
                EnginePoll.identifier: EnginePoll }

    def __new__(cls, hint, info):
        """
        Create a new preferred Engine.
        """
        if not hint or hint == 'auto':
            # 2010-02-11: disable automatic EngineEPoll selection as an
            # epoll issue has been found (trac ticket #56).
            for engine_class in [ EnginePoll ]:  # in order or preference
                try:
                    return engine_class(info)
                except EngineNotSupportedError:
                    pass
            raise RuntimeError("FATAL: No supported Engine found")
        else:
            # User overriding engine selection
            try:
                return cls.engines[hint](info)
            except KeyError, exc:
                print >> sys.stderr, "Invalid engine identifier", exc
                raise