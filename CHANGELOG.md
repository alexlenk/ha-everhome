# Changelog

## [0.4.2](https://github.com/alexlenk/ha-everhome/compare/v0.4.1...v0.4.2) (2025-09-05)


### Features

* add comprehensive test infrastructure and CI/CD pipeline ([fcc444b](https://github.com/alexlenk/ha-everhome/commit/fcc444b27c7d0ea53f806f97c672898f2521cf79))
* update Home Assistant to more recent version (2023.12.4) ([7035434](https://github.com/alexlenk/ha-everhome/commit/7035434cd3c11537fb914134f5da900cc2a1f004))
* upgrade to newer pytest-homeassistant-custom-component framework ([e58a92e](https://github.com/alexlenk/ha-everhome/commit/e58a92e4114ae97af1b86596ae347a28ec086c04))


### Bug Fixes

* configure flake8 to use 88 character line length matching black ([a309ec6](https://github.com/alexlenk/ha-everhome/commit/a309ec6daebfad6dddcfdd3dd2c960adf6e7a5ea))
* correct OAuth2 config flow handler inheritance for proper registration ([5929c05](https://github.com/alexlenk/ha-everhome/commit/5929c05b4d29ed0a472621e5aff7ebbd07c628ff))
* pin test dependencies to exact working versions ([a3daff4](https://github.com/alexlenk/ha-everhome/commit/a3daff46f7b4b7785a9c8f254bb5c046e378722b))
* remove unused imports to resolve flake8 linting errors ([563e031](https://github.com/alexlenk/ha-everhome/commit/563e03166bb1998c5473b230ae62ed0290660693))
* resolve aiohttp dependency conflict with Home Assistant ([40b96d8](https://github.com/alexlenk/ha-everhome/commit/40b96d853a69b160e0479238079f94d3dbcb614b))
* resolve aiohttp wheel build failure in GitHub Actions ([8a0da92](https://github.com/alexlenk/ha-everhome/commit/8a0da926307988d7e8ebf39e9c65a5d28f4f5a47))
* resolve all flake8 linting errors ([3cbff2f](https://github.com/alexlenk/ha-everhome/commit/3cbff2fcfde689483329f255a80121ec934b9df6))
* resolve all test failures with comprehensive HTTP mocking and API compatibility fixes ([0762c7e](https://github.com/alexlenk/ha-everhome/commit/0762c7ecdf35bb99ed00114a802caefd47997273))
* resolve black code formatting issues ([320064f](https://github.com/alexlenk/ha-everhome/commit/320064f0cede4128f58346036ae92fe8e576fa5f))
* resolve mypy error in config flow handler inheritance ([c54b6d9](https://github.com/alexlenk/ha-everhome/commit/c54b6d913774226e7e08ca8decd3da0b2a06f378))
* resolve mypy type annotation errors ([a825210](https://github.com/alexlenk/ha-everhome/commit/a8252107c9c2550765a2db82b0fab828f86a05b9))
* revert to Home Assistant 2023.1.7 required by test framework ([6f97f72](https://github.com/alexlenk/ha-everhome/commit/6f97f720bfca32e71462962e86de1194897f7fc9))
* solve async context manager mocking issues in coordinator tests ([d29a4e5](https://github.com/alexlenk/ha-everhome/commit/d29a4e5b35cd1900e11a38b2a246d2e7ad32ac31))
* update Home Assistant API compatibility and improve error handling ([e826064](https://github.com/alexlenk/ha-everhome/commit/e826064a3ef4453612d09cbaeadf812d7a8fff9d))


### Documentation

* add test status and codecov badges to README ([4c2fd3f](https://github.com/alexlenk/ha-everhome/commit/4c2fd3f97f6701c87dfb9ccc66ca32dac755137c))

## [0.4.1](https://github.com/alexlenk/ha-everhome/compare/v0.4.0...v0.4.1) (2025-08-02)


### Features

* add professional GitHub Actions workflows and automated release management ([700edc6](https://github.com/alexlenk/ha-everhome/commit/700edc691d74cbc15bd6602d08b28e20f94bb72d))
* expand shutter-type device support and update documentation ([0e99ff9](https://github.com/alexlenk/ha-everhome/commit/0e99ff94fa2880e38e90530c5ef7d58107b2142a))
* re-enable Release Please workflow after repository settings fix ([aaf145e](https://github.com/alexlenk/ha-everhome/commit/aaf145e7a6192aacc1bf00145e479803aaa2b020))


### Bug Fixes

* disable automatic Release Please to prevent CI failures ([3007f89](https://github.com/alexlenk/ha-everhome/commit/3007f89cd99ef2a551fd1d78d1efcf3cbb668af8))
* disable labeling in Release Please to prevent permission errors ([85eb3ec](https://github.com/alexlenk/ha-everhome/commit/85eb3ec4dd3514aa62dec95a3900efb19bffcb2f))
* resolve Hassfest validation issues ([9f6791a](https://github.com/alexlenk/ha-everhome/commit/9f6791a067e492081907b89f3f0941d9921ca035))
* update Release Please workflow configuration ([39af9fc](https://github.com/alexlenk/ha-everhome/commit/39af9fcdd07a5d3e1b4bcaafdd239c2249ef4558))
