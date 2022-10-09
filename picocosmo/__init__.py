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
_version_suffix = 'rc1'  # for suffixes such as 'rc' or 'beta' or 'alpha'
__version__ = _version_info._get_version_string()
__version__ += _version_suffix

# Import components to be callabel at package level
__all__ = ["runCosmoDAQ", "PulseFilter", "runCosmoUi"]


