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
    <img src="docs/images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Telegram-UI</h3>

  <p align="center">
    A Telegram project to upload files in a Telegram channel and use it as a cloud storage
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

[![Product Name Screen Shot][product-screenshot]]

This is a simple project written in Python to upload files to Telegram. The idea come from my passion for drone and videos. I started to take a lot of videos while flying my FPV drone and a lot of them are useless but i did't want to trash them as they are a part of my learning process. So i decided to build this software that allow me to keep them and be able to always watch them



<!-- BUILT WITH -->
### Built With

[![Python][Python]][Python-url]
[![Tkinter][Tkinter]][Tkinter-url]
[![Telegram][Telegram]][Telegram-url]
[![FFMPEG][FFMPEG]][FFMPEG-url]



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

Run the application by executing the main.py file in the src folder

```bash
python src/main.py
```


<!-- ROADMAP -->
## Roadmap
 
Features to add:
- [X] Add the download part
- [X] Change the file image with a preview
- [X] Automatically download FFMPEG
- [X] Add a move function
- [X] Add a sync job list to handle sync jobs
- [ ] Add a Docker image
- [ ] Add robust MIME type detection and handler plugins for all file types
- [ ] Fullscreen / large preview with native player (video/audio/image)
- [ ] Transactional file operations with rollback support
- [ ] Automatic cleanup when a Telegram message is deleted or errors occur
- [ ] Add resumable and chunked uploads/downloads to improve reliability
- [ ] Implement retry/backoff and network error handling for transfers
- [ ] Add structured logging, configurable log levels, and error reporting
- [ ] Add unit and integration tests; enforce with CI (GitHub Actions)
- [ ] Add code formatting and linting (Black, isort, flake8/ruff)
- [ ] Refactor to modules, add typing hints and docstrings
- [ ] Add a Settings UI and persistent configuration (JSON or TOML)
- [ ] Add performance profiling and benchmarks for upload/download paths
- [X] Provide packaging: single-file executable and optional pip package
        DONE. It will create a dist folder with the installer. To execute run telegram-ui on the CLI
- [ ] Add better progress UI, notifications, and clearer error messages
- [ ] Improve UI/UX and accessibility (keyboard navigation, contrast)
- [ ] Add an examples/usage docs folder and tutorial walkthroughs
- [ ] Improve the download speed (Now it's really slow but if download from web.telegram it is fast)
- [ ] Improve the upload speed (Now it's slow but if upload from web.telegram it is fast)


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



<!-- CODE STYLE RULES -->
## Code Style Rules

Follow these rules when adding or changing Python code in this repository:

- **Docstring format:** Function and method docstrings must use an Args/Returns style and the text must start on the line after the opening triple quotes. Do not end docstring phrases with a period.

- **Docstring sections:** Use the exact section headers `Args` and `Returns` (capitalized) and list parameters and return values under them.

- **Return type annotation:** Every function and method must include an explicit return type annotation (for example `-> None`, `-> str`, or `-> FileMessage`). Use forward references (strings) or `from __future__ import annotations` when needed to avoid circular import issues.

- **No trailing punctuation:** Do not add a period at the end of short docstring phrases or bullet-like lines.

Example docstring style:

```
def example(x: int) -> str:
  """
  Example function

  Args:
    x: the input integer

  Returns:
    the resulting string
  """
  return str(x)
```

Additional rules:

- **Type hints for parameters:** All function and method parameters should include type annotations whenever practical.

- **Module-level deferred annotations:** Prefer `from __future__ import annotations` at the top of modules to avoid circular imports and enable forward references.

- **Avoid mutable default arguments:** Do not use mutable objects (lists, dicts, sets) as default parameter values. Use `None` and initialize inside the function.

- **Formatting and linting:** The project follows Black formatting (88-char line length). Run `black .` and `isort .` before committing. Use `ruff` or `flake8` for linting where helpful.

- **Logging:** Use the `logging` module instead of `print()` for runtime messages. Tests and small scripts may use `print` temporarily.

- **Errors and exceptions:** Raise specific exceptions and avoid broad `except: pass` silence. If catching broad exceptions, log them.

- **Naming:** Use descriptive variable and function names. Avoid single-letter names except for obvious counters (`i`, `j`).

- **Testing:** Add unit tests for new functionality. Place tests under `tests/` and run them with `pytest`.

- **Commits:** Write clear commit messages and reference issue numbers when applicable.

### Naming conventions

Follow these naming rules (aligned with Python conventions) unless a strong reason exists to deviate:

- **Classes:** Use PascalCase (e.g., `MyAwesomeClass`).
- **Functions and methods:** Use snake_case (e.g., `do_something`). Avoid camelCase unless interoperating with external APIs or following an existing code style in a small localized module.
- **Variables and parameters:** Use snake_case for normal variables. Constants: UPPER_SNAKE_CASE.
- **Private/internal members:** Use a single leading underscore for internal/private attributes or methods (e.g., `_helper`). Use double leading underscores (`__name`) only when you need name mangling — avoid unless necessary.
- **Modules and packages:** Use lowercase names; modules may use underscores (e.g., `file_manager`).
- **Attributes and properties:** Use snake_case; prefer properties over bare attributes for computed values.
- **Verb vs noun:** Function names should be verbs or verb phrases; class names should be nouns.
- **Avoid Hungarian/camel hybrid:** Prefer descriptive names over abbreviated or camel-style identifiers.


<!-- LICENSE -->
## License

Distributed under the MIT License.



<!-- CONTACT -->
## Contact

Armillotta Martino - [@martinoarmillotta](https://www.instagram.com/martinoarmillotta/) - armillottamartino@gmail.com




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
[product-screenshot]: docs/images/screenshot.png

[Python]: https://img.shields.io/badge/python-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Python-url]: https://www.python.org/
