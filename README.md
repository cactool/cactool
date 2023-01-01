<a href="#readme">![Cactool](https://i.imgur.com/XooF3N8.png)</a>

# Cactool
<p align="center">
 <a href="https://badge.fury.io/py/Cactool">
  <img src="https://badge.fury.io/py/Cactool.svg" alt="PyPI version">
 </a>
  <a href="https://cactool.readthedocs.io">
  <img src="https://readthedocs.org/projects/cactool/badge/?version=latest&style=flat" alt="docs">
 </a>
  <a href="https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta">
  <img src="https://img.shields.io/badge/stability-beta-33bbff.svg" alt="stability-beta">
 </a>
  <a href="">
  <img src="https://github.com/cactool/cactool/workflows/CodeQL/badge.svg" alt="CodeQL">
 </a>
 </p>

# Introduction
Cactool (or Content Analysis Coding Tool) is a platform which allows researchers to collaboratively code pre-existing social media datasets in their native format for manual content and discourse analysis.

Using Cactool is easy, after the initial installation, you can create users, import your data, set your coding variables, and get started! This allows coders, especially those working in groups, to analyse social media data quicker, more accessibly, and more accurately by viewing posts in context.

# Features

- **No more coding via spreadsheets:** Coding via your browser (tested working on Chrome, Firefox, Edge, & Safari) with posts visible as they would be on the social media platform. This allows your coders to evaluate social media content in their native format.
- **Simple Import and Export:** Take your pre-existing social media URLs from software such as [4Cat](https://github.com/digitalmethodsinitiative/4cat), [NodeXL](https://www.smrfoundation.org/nodexl/), or API Scrapers such as [Tweepy](https://www.tweepy.org/) and import them as a CSV list. When done, you can export your data via CSV to whatever analysis software you desire.
- **Importing of image/text data:** Have data from secondary source with no URLs? No Problem.
- **Manage Multiple Datasets:** Want to split your project by source/themes? You can manage multiple concurrent datasets at the same time.
- **Built for collaboration:** Cactool comes pre-packaged with user management; codes attributed are attributed to each coder for coder reliability calculation (such as [ReCal](http://dfreelon.org/utils/recalfront/)). Multiple people can be coding at the same time without sharing documents. No need to worry about version control or splitting up data.
- **Code on the Go:** Cactool is mobile friendly and can be accessed remotely (we recommend using a VPN to connect, see our tutorial for why). This provides researchers interested in social media content and spaciality new avenues of research.

## Platform Compatability

Cactool works for across multiple-social media platforms. The following data types are currently supported:
- Twitter
- YouTube
- TikTok
- Instagram
- Mastodon (via OEmbed)
- Image Data (Photos/screenshots)
- Text Strings
- & Some* compatibility with other OEmbed platforms


# Documentation
Easy to follow installation instructions and user guides can be found via the documentation on [Read the Docs](https://cactool.readthedocs.io)

# Installation and usage
You can install Cactool on your local machine or on a server through [Docker](https://www.docker.com/) or directly using [PIP (package manager)](https://pip.pypa.io/en/stable/). Running Cactool through a server is useful if you want to have multiple coders, or want to code through your mobile while situated away from your main computer. 

Cactool also has some custom build configurations

## Docker
### 1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop), and start it. 
Note that on Windows, you may need to ensure that WSL (Windows Subsystem for Linux) integration is enabled in Docker. You can find this in the Docker setting in Settings -> Resources-> WSL Integration -> Enable integration with required distros.
### 2. Clone the repository
```bash
git clone https://github.com/cactool/cactool
```
### 3. Enter the cactool directory
```
cd cactool
```
### 4. Run `docker-compose`
Make sure the Docker daemon is running then run
```bash
docker-compose up -d
```
An instance should be accessible on port 80

## Directly (with Pip)
### 1. Install Cactool
```bash
pip install cactool
```
### 2. Start the website
```bash
cactool
```
The server will be running on port 80

## Custom Builds
There are some additional configuration settings available. For example those aimed at low-memory machines (such as installing Cactool on a Raspberry Pi), or server users with a public facing instance (such as custom ports, limiting file size uploads, and limiting user-signups. Please read the documents for more.

# Credits
The project’s Principle Investigator is [Dr Liam McLoughlin](https://Leelum.com), *Lecturer in Media & Communication at the University of Liverpool*, and development was undertaken by [Sam Ezeh](https://github.com/dignissimus)

## Funding
Cactool Development was funded by the University of Liverpool’s Research Development and Initiative Fund (RDIF).
<div align="center">![UoL - Logo - CMYK](https://user-images.githubusercontent.com/11173283/210178161-3070e2df-68a8-4128-8b1b-43453571c85b.png)</div>




## Citations
### Bibtex
```bibtex
@software{McLoughlin_Ezeh_2022,
  title = {{Cactool: An easy way to collaboratively code social media posts for manual content and discourse analysis (BETA)}},
  author  = {McLoughlin, Liam and Ezeh, Sam},
  year  = {2022},
  doi = {10.5281/zenodo.6070206},
  url = {https://github.com/cactool/cactool},
  license = {MIT}
}
```
### APA
```
McLoughlin, L., & Ezeh, S. (2022). Cactool: An easy way to collaboratively code social media posts for manual content and discourse analysis (BETA). [Computer software]. URL:https://github.com/cactool/cactool
```

# Images
![Importing from CSV and setting the coding questions made easy](https://user-images.githubusercontent.com/11173283/191358197-1119d00b-5088-485e-9d13-726da1c9708c.png)



![Coding & Exporting of data](https://user-images.githubusercontent.com/11173283/191358390-9b903d61-161a-44ea-8bb8-8bc060c520bd.png)



![Multiple data types](https://user-images.githubusercontent.com/11173283/191358480-d46348c7-fd74-4378-b952-7a16c01aa82e.png)



# Outputs
If you've used or cited Cactool in your research, please let us know and we will highlight your paper below. It also helps us understand who and how it's being used!
- The development of Cactool has also resulted in features being added to Python 3.11. ["bpo-14265: Adds fully qualified test name to unittest output (GH-32138)"](https://github.com/python/cpython/commit/755be9b1505af591b9f2ee424a6525b6c2b65ce9)
