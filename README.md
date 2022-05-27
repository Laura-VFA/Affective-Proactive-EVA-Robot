# Eva-Assistant-Python

EVA is a **social 🗣 and affective ❤️ robot** aimed at assisting older adults in conducting Instrumental Activities of Daily Living (IADLs). It is not only a passive assistant, but an active one: **proactive behaviour** is incorporated in the robot. It can start conversations and show concern about the user, making the interaction more natural and affective.  
This repo contains the *brain* 🧠 structure of the robot, the proactive and interaction behavior themselves.
<p align="center">
  <img src="https://user-images.githubusercontent.com/72492679/169651452-13529463-92b5-4fc1-bb0c-9b8303c46024.png" width="300"/>
</p>

## Main components 🤖

EVA is constructed using the following elements:
- [Screen Waveshare 5.5" HDMI AMOLED](https://www.waveshare.com/5.5inch-hdmi-amoled.htm)
- [Intel® RealSense™ Depth Camera D435i](https://www.intelrealsense.com/depth-camera-d435i/)
- [Raspberry Pi 4 Model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
- [Matrix Voice](https://www.matrix.one/products/voice)
- [Tempest M10 RGB Hero 2.0 Gaming Speakers](https://www.tempestofficial.com/inicio/38-speakers-m10-rgb-hero-20.html)
- Plastic structure printed using 3D printer

It is not compulsory to have exactly the same components, as long as they have the same functionalities. If you change any of them, make sure you have the correct drivers. In particular, if camera is changed, camera frames capturing code must be rewritten to use the suitable library for your camera management (it will probably not be [*pyrealsense2*](https://pypi.org/project/pyrealsense2/)).

## Built with 🛠️

*Coming soon.* 🔜

## Installation ⚙️

### Requirements

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all the pre-requisites.

```bash
pip3 install -r requirements.txt
```

### Google and IBM services
Ensure you have [IBM Cloud](https://cloud.ibm.com/) and [Google Cloud](https://console.cloud.google.com/) accounts.  

It is necessary to have *apikeys* 🔑 for the following services:
- [Google Speech to Text](https://cloud.google.com/speech-to-text/docs/libraries)
- [Google Text to Speech](https://cloud.google.com/text-to-speech/docs/libraries)
- [Google Translator](https://cloud.google.com/translate/docs/basic/translating-text#translating_text)
- [IBM Natural Language Understanding](https://cloud.ibm.com/apidocs/natural-language-understanding?code=python)
- [IBM Watson Assistant](https://cloud.ibm.com/apidocs/assistant/assistant-v2?code=python)

Both files (Google credentials and IBM credentials) must be stored in a ```credentials/``` directory, located outside the main project directory:
```bash
$ any_directory
.
├── credentials
│   ├── google_credentials.json
|   ├── assistant_credentials.json
│   └── ibm_credentials.env
└── Eva-Assistant-Python/
```
In this case, by-default environment variables provided by Google and IBM (*GOOGLE_APPLICATION_CREDENTIALS* and *IBM_CREDENTIALS_FILE*) are used for automatic services apikey authentication (easier!). Also, a *WATSON_ASSISTANT_CREDENTIALS* variable containing *assistant_credentials.json* path is used for obtaining the assistant id.

**WARNING ⚠️**: IBM Watson Assistant dialog tree can be freely designed by the user. This makes more flexible and customized the user interaction with your own robot 😉

### Telegram service

*Coming soon.* 🔜

## Usage 🚀

```bash
python3 main.py
```

## Authors 📝
- [Laura Villa 🦁](https://github.com/Laura-VFA)
