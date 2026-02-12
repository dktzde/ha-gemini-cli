The Home Assistant frontend is built using web components. For more background about our technology choices, [see this blog post](https://developers.home-assistant.io/blog/2019/05/22/internet-of-things-and-the-modern-web.html).

Do not use development mode in production. Home Assistant uses aggressive caching to improve the mobile experience. This is disabled during development so that you do not have to restart the server in between changes.

## Setting up the environment

Follow our [devcontainer development environment](/docs/setup_devcontainer_environment) guide to set up a proper development environment first.

### Getting the code

The first step is to fork the [frontend repository][hass-frontend] and add the upstream remote. You can place the forked repository anywhere on your system.

```shell
git clone git@github.com:YOUR_GIT_USERNAME/frontend.git
cd frontend
git remote add upstream https://github.com/home-assistant/frontend.git
```

### Configuring Home Assistant

You will need to have an instance of Home Assistant set up. For a development instance see our guide on [setting up a development environment](/development_environment.mdx).

There are two ways to test the frontend. You either run a development instance Home Assistant Core, or you configure the frontend to connect to an existing Home Assistant instance. The first option is how it will work in production. The second allows running a development frontend against an existing Home Assistant with minimal interference. The downside is that not everything can be tested this way. For example, the login page will always be the one built-in into your Home Assistant.

import Tabs from '@theme/Tabs'
import TabItem from '@theme/TabItem'

### Installing Node.js (manual environment only)

Node.js is required to build the frontend. The preferred method of installing node.js is with [nvm](https://github.com/nvm-sh/nvm). Install nvm using the instructions in the [README](https://github.com/nvm-sh/nvm#install--update-script), and install the correct node.js by running the following command:

```shell
nvm install
```

[Yarn](https://yarnpkg.com/en/) is used as the package manager for node modules. [Install yarn using the instructions here.](https://yarnpkg.com/getting-started/install)

### Install development dependencies and fetch latest translations

Bootstrap the frontend development environment by installing development dependencies and downloading the latest translations.

```shell
nvm use
script/bootstrap
script/setup_translations
```

This needs to be done manually, even if you are using dev containers. Also, you will be asked to enter a code and authorize the script to fetch the latest translations.

In case a previous authorization no longer works (e.g. you see a "Bad Credentials" error during translation fetching), delete the `token.json` file in the `translations` folder and execute `script/setup_translations` again to retrigger the authorization process.

If you are using a development container, run these commands inside the container.

## Development

### Run development server

Run this script to build the frontend and run a development server:

```shell
nvm use
script/develop
```

When the script has completed building the frontend, and Home Assistant Core has been set up correctly, the frontend will be accessible at `http://localhost:8123`. The server will automatically rebuild the frontend when you make changes to the source files.

### Run development frontend over existing HA instance

Run this command to start the development server:

```shell
nvm use
script/develop_and_serve -c https://homeassistant.local:8123
```

You may need to replace "https://homeassistant.local:8123" with your local Home Assistant url.

### Browser settings

Open Google Chrome's Developer tools, and make sure you have cache disabled and correct settings to avoid stale content:

Instructions are for Google Chrome

1. Disable cache by ticking the box in **Network** > **Disable cache**

  

2. Enable Bypass for network in **Application** > **Service Workers** > **Bypass for network**

  

## Creating pull requests

If you're planning on issuing a PR back to the Home Assistant codebase you need to fork the frontend project and add your fork as a remote to the Home Assistant frontend repo.

```shell
git remote add fork <github URL to your fork>
```

When you've made your changes and are ready to push them change to the working directory for the frontend project and then push your changes

```bash
git add -A
git commit -m "Added new feature X"
git push -u fork HEAD
```

## Building the frontend

If you're making changes to the way the frontend is packaged, it might be necessary to try out a new packaged build of the frontend in the main repository (instead of pointing it at the frontend repo). To do so, first build a production version of the frontend by running `script/build_frontend`.

To test it out inside Home Assistant, run the following command from the main Home Assistant repository:

```shell
pip3 install -e /path/to/hass/frontend/ --config-settings editable_mode=compat
hass --skip-pip-packages home-assistant-frontend
```

[hass-frontend]: https://github.com/home-assistant/frontend
