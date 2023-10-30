# utils

Documentation: [https://ftrackhq.github.io/integrations/libs/utils/](https://ftrackhq.github.io/integrations/libs/utils/)

## Installation

```bash
  pip install ftrack-utils
```

## Building


### CI build

See Monorepo build CI

### Manual build

Go to the root of the utils package within monorepo:

```bash
    cd integrations/libs/utils
```


Set or bump version in pyproject.toml:

```bash
    poetry version prerelease
```
or:

```bash
    poetry version patch
```

or:

```bash
    poetry version minor
```
or:
```bash
    poetry version major
```


Build with Poetry:
    
```bash
    poetry build
```

