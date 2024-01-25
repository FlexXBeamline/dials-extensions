# dials-extensions
Extensions to DIALS / dxtbx for data collected at CHESS beamline ID7B2

## Installation

With the DIALS environment activated:

```bash
libtbx.python -m pip install git+https://github.com/FlexXBeamline/dials-extensions
```

To check whether the custom format is available:

```bash
dxtbx.show_registry | grep "CHESS"
```

The following formats are expected:
```
    4          FormatCBFMiniPilatusCHESS_6MSN127
    5            FormatNXmxEigerFilewriterCHESS
    6              FormatNXmxEigerFilewriterCHESS
```