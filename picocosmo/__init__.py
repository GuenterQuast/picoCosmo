"""

.. moduleauthor:: Guenter Quast <guenter.quast@online.de>

.. module picocosmo
   :synopsis: analyze data from Cosmo Detectors and Kamiokanne
       by Netzwerk Teilchenwelt with picoScope USB device

.. moduleauthor:: Guenter Quast <Guenter.Quast@online.de>

**picocosmo**
    analyze data from Cosmo Detectors and Kamiokanne
    by Netzwerk Teilchenwelt with picoScope USB device

    display online signal wave-forms, filter signals and
    search for coincidences and double pulses, display
    rates and store raw data, wave-form pictures or
    pulse features in files
"""

# Import version info
from ._version_info import *

# and set version
__version__ = _version_info._get_version_string()

# Import components to be callabel at package level
__all__ = ["runCosmoDAQ", "PulseFilter", "runCosmoUi"]
