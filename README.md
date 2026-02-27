# Everhome Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Test][test-shield]][test]
[![codecov][codecov-shield]][codecov]

_Integration to control Everhome devices in Home Assistant._

## About Everhome

[Everhome](https://everhome.cloud) is a cloud-based smart home platform that supports various device manufacturers and protocols (433 MHz, 868 MHz, ZigBee).

## Supported Device Categories

**This component will set up the following platforms:**

| Platform | Description | Hardware tested |
| -------- | ----------- | --------------- |
| `cover`  | Shutters, blinds, awnings, curtains, and garage doors | ✅ Yes |
| `binary_sensor` | Door/window contacts, motion, smoke, and water detectors | ⚠️ No — API-based only |
| `light` | On/off and dimmable lights | ⚠️ No — API-based only |
| `switch` | Smart sockets and irrigation valves | ⚠️ No — API-based only |

> **Note:** Only the `cover` platform has been tested with real hardware (Jarolift motors via Everhome CloudBox). The `binary_sensor`, `light`, and `switch` platforms are implemented based on the Everhome API documentation and have not been verified against physical devices. If you own Everhome-compatible sensors, lights, or sockets and can test them, please open an issue or pull request with feedback.

### Tested Brands and Motors

The integration has been tested and verified with:
- **[Jarolift](https://www.jarolift.de/)** - German manufacturer of tubular motors and drive systems
- **Other Everhome-compatible** shutter motor brands

## Features

- **OAuth2 Authentication** - Secure connection to Everhome cloud
- **Real-time Control** - Open, close, and stop shutter operations
- **State Detection** - Intelligent state management with API limitations handling
- **Universal Shutter Support** - Compatible with all Everhome shutter-type devices
- **Multiple Device Categories** - Support for shutters, blinds, awnings, and curtains
- **Always-Available Controls** - All buttons remain active regardless of state
- **Position Feedback** - Position reporting when available from devices
- **Reliable Operation** - Graceful handling of local remote usage and API outages

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the "+" button
4. Search for "Everhome"
5. Download the integration
6. Restart Home Assistant

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
2. If you do not have a `custom_components` directory (folder) there, you need to create it
3. In the `custom_components` directory (folder) create a new folder called `everhome`
4. Download _all_ the files from the `custom_components/everhome/` directory (folder) in this repository
5. Place the files you downloaded in the new directory (folder) you created
6. Restart Home Assistant

## Configuration

### Initial Setup

1. In Home Assistant, go to **Configuration** → **Integrations**
2. Click **"+ Add Integration"**
3. Search for **"Everhome"**
4. Follow the OAuth2 authentication flow:
   - You'll be redirected to Everhome's login page
   - Log in with your Everhome credentials
   - Authorize Home Assistant to access your account
   - You'll be redirected back to Home Assistant

### Supported Devices

The integration automatically discovers and configures all shutter-type devices:
- **Shutters** - Motorized window shutters from any compatible manufacturer
- **Blinds** - Motorized window blinds and venetian blind systems  
- **Awnings** - Outdoor shade awnings and retractable canopy systems
- **Curtains** - Motorized curtain and drape systems
- **Garage Doors** - Motorized garage door systems

#### Manufacturer Compatibility

This integration works with shutter-type devices from various manufacturers connected to Everhome, including:
- **Jarolift** - TDEF series tubular motors, Smart WiFi motors, and 433 MHz radio systems
- **Other brands** - Any shutter motor system compatible with the Everhome platform

**Universal Shutter Features Supported:**
- Manual remote control detection and state synchronization
- Motor limit position handling for all compatible systems
- Emergency stop functionality across all device types
- Integration with manufacturer-specific protocols via Everhome

### Device Features

Each device provides:
- **Open/Close Controls** - Basic shutter operation
- **Stop Function** - Emergency stop capability
- **Position Reporting** - Current position when available (0-100%)
- **State Feedback** - Opening, closing, open, closed states
- **Device Information** - Model, firmware version, manufacturer details

## Known Limitations

### API Constraints
- **No Intermediate Positions**: Everhome API doesn't provide percentage positions for most devices due to motor limitations
- **Local Remote Interference**: Using physical remotes can cause temporary state sync issues as the cloud API doesn't receive these updates immediately
- **Position Accuracy**: Some devices may report approximate positions rather than exact percentages

### Workarounds Implemented
- **Smart State Detection**: Uses explicit API states when available, falls back to position-based detection
- **Motor Threshold Handling**: Treats positions ≤5% as closed and ≥95% as open to handle motor limitations
- **Graceful Degradation**: Maintains control functionality even when state data is unavailable

## Usage Examples

### Basic Automation
```yaml
automation:
  - alias: "Close shutters at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: cover.close_cover
      target:
        entity_id: cover.bedroom_shutter

  - alias: "Open shutters at sunrise"
    trigger:
      platform: sun
      event: sunrise
    action:
      service: cover.open_cover
      target:
        entity_id: cover.bedroom_shutter
```

### Position-Based Control
```yaml
automation:
  - alias: "Partial shade during hot days"
    trigger:
      platform: numeric_state
      entity_id: sensor.outdoor_temperature
      above: 30
    action:
      service: cover.set_cover_position
      target:
        entity_id: cover.living_room_awning
      data:
        position: 75  # 75% extended for shade
```

## Troubleshooting

### Authentication Issues
- **Invalid Credentials**: Verify your Everhome account credentials
- **OAuth Timeout**: Try the authentication process again
- **Token Expiration**: The integration automatically handles token refresh

### Device State Issues
- **"Unknown" States**: Fixed in recent versions - update to latest release
- **Delayed Updates**: Local remote usage may cause temporary delays
- **Missing Devices**: Ensure devices are properly configured in the Everhome app

### Connection Problems
- **API Timeouts**: Check internet connectivity and Everhome service status
- **Rate Limiting**: The integration respects API rate limits automatically
- **Cloud Outages**: Integration will retry automatically when service resumes

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: warning
  logs:
    custom_components.everhome: debug
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) first.

### Development Setup
1. Fork this repository
2. Create a development branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Reporting Issues
- Use the [issue tracker](https://github.com/alexlenk/ha-everhome/issues)
- Include Home Assistant version, integration version, and debug logs
- Describe expected vs actual behavior

## Roadmap

### Planned Features
- **CI/CD Pipeline** - Automated testing and releases ✅ (Completed)
- **Binary Sensors** - Door/window contacts, motion, smoke, water detectors ✅ (Completed, untested on hardware)
- **Lights** - On/off and dimmable light control ✅ (Completed, untested on hardware)
- **Switches** - Smart sockets and irrigation valves ✅ (Completed, untested on hardware)
- **Climate** - Heating/cooling thermostat support
- **Sensors** - Energy meters, solar inverters, environment sensors
- **Group Control** - Synchronized operation of multiple devices
- **Advanced Diagnostics** - Better error reporting and device health monitoring

### Future Considerations
- **Local API Support** - If Everhome provides local connectivity options
- **Scene Integration** - Predefined scenes for different times of day
- **Camera** - IP camera stream support (blocked on undocumented stream URL)

## Credits

This integration was created by [@alexlenk](https://github.com/alexlenk).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

[releases-shield]: https://img.shields.io/github/release/alexlenk/ha-everhome.svg?style=for-the-badge
[releases]: https://github.com/alexlenk/ha-everhome/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/alexlenk/ha-everhome.svg?style=for-the-badge
[commits]: https://github.com/alexlenk/ha-everhome/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/alexlenk/ha-everhome.svg?style=for-the-badge
[test-shield]: https://img.shields.io/github/actions/workflow/status/alexlenk/ha-everhome/test.yml?style=for-the-badge&label=Tests
[test]: https://github.com/alexlenk/ha-everhome/actions/workflows/test.yml
[codecov-shield]: https://img.shields.io/codecov/c/github/alexlenk/ha-everhome?style=for-the-badge
[codecov]: https://codecov.io/gh/alexlenk/ha-everhome