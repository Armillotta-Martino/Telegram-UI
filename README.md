[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Armillotta-Martino/Telegram-UI">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Telegram-UI</h3>

  <p align="center">
    A Telegram project to upload videos in a Telegram channel and use it as a cloud storage
    <br />
    <br />
    <a href="https://github.com/Armillotta-Martino/Telegram-UI/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/Armillotta-Martino/Telegram-UI/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

This is a simple project written in Python to upload files to Telegram. The idea come from my passion for drone and videos. I started to take a lot of videos while flying my FPV drone and a lot of them are useless but i did't want to trash them as they are a part of my learning process. So i decided to build this software that allow me to keep them and be able to always watch them



### Built With

This section should list any major frameworks/libraries used to bootstrap your project. Leave any add-ons/plugins for the acknowledgements section. Here are a few examples.

[![Python][Python]][Python-url]



<!-- GETTING STARTED -->
## Getting Started

Follow these steps to set up and run **Telegram-UI** locally on your machine.

### Prerequisites

Make sure you have **Python 3.10+** installed.  
Then, create and activate a virtual environment:

#### 🪟 Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

python3 -m venv venv
source venv/bin/activate

### Installation

Clone the repository

```bash
git clone https://github.com/Armillotta-Martino/Telegram-UI.git
cd Telegram-UI
```

Install dependencies

```bash
pip install -r requirements.txt
```

Get your Telegram API credentials:

Go to https://my.telegram.org and log in with your Telegram account.
Click API development tools.
Create a new application and note down your API_ID and API_HASH.
These will be needed for the app to connect to Telegram.

(Optional) Configure environment variables
Create a copy of .env_example and rename it to .env, then change the values with your values from Telegram API

Run the application

```bash
python src/main.py
```


<!-- ROADMAP -->
## Roadmap

- [ ] Add the download part
- [ ] Change the file image with a preview
- [X] Automatically download FFMPEG
- [ ] Design a better UI
- [ ] Add a move function
- [ ] Be able to handle every type of file
- [ ] Add the possibility of open a big preview of the file

- [ ] Add a transaction system to undo all the changes if something go wrong
- [ ] Add the code to clear the folder system if a message has been deleted or has a error

See the [open issues](https://github.com/Armillotta-Martino/Telegram-UI/issues) for a full list of proposed features (and known issues).

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- LICENSE -->
## License

Distributed under the MIT License.



<!-- CONTACT -->
## Contact

Armillotta Martino - [@martinoarmillotta]([https://twitter.com/your_username](https://www.instagram.com/martinoarmillotta/)) - armillottamartino@gmail.com




<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/Armillotta-Martino/Telegram-UI.svg?style=for-the-badge
[contributors-url]: https://github.com/Armillotta-Martino/Telegram-UI/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Armillotta-Martino/Telegram-UI.svg?style=for-the-badge
[forks-url]: https://github.com/Armillotta-Martino/Telegram-UI/network/members
[stars-shield]: https://img.shields.io/github/stars/Armillotta-Martino/Telegram-UI.svg?style=for-the-badge
[stars-url]: https://github.com/Armillotta-Martino/Telegram-UI/stargazers
[issues-shield]: https://img.shields.io/github/issues/Armillotta-Martino/Telegram-UI.svg?style=for-the-badge
[issues-url]: https://github.com/Armillotta-Martino/Telegram-UI/issues
[license-shield]: https://img.shields.io/github/license/Armillotta-Martino/Telegram-UI.svg?style=for-the-badge
[license-url]: https://github.com/Armillotta-Martino/Telegram-UI/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555

[linkedin-url]: https://www.linkedin.com/in/martino-armillotta-702a1316a/
[product-screenshot]: images/screenshot.png

[Python]: https://img.shields.io/badge/python-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Python-url]: https://www.python.org/
