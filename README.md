# Cognitive Robotics HRI Pepper
Cognitive Robotics framework for Human-Robot Interaction (HRI) based on ROS. It integrates deep learning models for person, face, and emotion detection with a Rasa-powered chatbot to enable social intelligence on the Pepper robot.

# ROS - Pepper Integration 

A ROS (Robot Operating System) project featuring integration with the Pepper humanoid robot, including camera and microphone support for human-robot interaction.

## 📋 Prerequisites

- ROS (Robot Operating System)
- Pepper robot (optional - can run in simulation mode)
- Configured ROS workspace

## 🚀 Quick Start

### Running with Pepper Robot

If you have access to a physical Pepper robot:

```bash
roslaunch all all.xml
```

### Running without Pepper Robot

To run the system in simulation mode without the physical robot:

```bash
roslaunch all all.xml pepper_on:=False pepper_camera_on:=False mic_index:=None
```

## 🔧 Troubleshooting

If the program fails to start, you may need to configure the ROS environment properly. Execute the following commands:

```bash
chmod +x devel/_setup_util.py
source devel/setup.bash
```

After running these commands, retry launching the main program.

## ⚙️ Configuration Parameters

The launch file accepts the following parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pepper_on` | `True` | Enable/disable Pepper robot connection |
| `pepper_camera_on` | `True` | Enable/disable Pepper's camera |
| `mic_index` | Auto | Microphone device index for audio input |

## 🏗️ System Architecture

This project provides a complete ROS-based system that can operate both with and without the Pepper robot hardware, making it suitable for:

- Development and testing without physical hardware
- Full deployment with Pepper robot
- Simulation and demonstration purposes

## 📝 Notes

- Ensure your ROS workspace is properly sourced before running the launch files
- When running without Pepper, all robot-specific functionalities will be disabled
- Check that all required ROS packages are installed and dependencies are met

## 🐛 Common Issues

**Issue**: Launch file not executing
- **Solution**: Run the setup commands in the Troubleshooting section

**Issue**: Microphone not detected
- **Solution**: Specify the correct `mic_index` parameter or set it to `None` to disable audio

**Issue**: Cannot connect to Pepper
- **Solution**: Verify network connection and Pepper's IP address configuration

## 📧 Contact

For questions, issues, or contributions, please open an issue on GitHub.

---

*Developed as final project of Cognitive Robotics course of the University of Salerno*

