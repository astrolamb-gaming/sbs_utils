# SBS Utils
This is a lower level part of the system written in pure python.

The MAST runtime uses this functionality.

The sbs utils aspects can be used without MAST as well.
So creating pure python scripts can be created, and use many of the functions used by MAST.

Python coding can be more complex than MAST, but if you know python you may find this method useful.


## Engine event processing
The {{ab.ac}} engine calls into python calling the function `cosmos_event_handler`.

For sbs_utils this is defined in the file [handler_hooks.py](https://github.com/artemis-sbs/sbs_utils/blob/master/sbs_utils/handlerhooks.py). This gets implemented by importing the sbs_utils library from your script.py A bit of python magic makes this happen.

