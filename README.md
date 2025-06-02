# Discord ReactBot SelfBot 🤖💬

A very simple SelfBot that allows auto reactions and has the ability to mass react with multiple emojis

> ⚠️ Be aware that you can get rate limited if you like reactbot multiple members, I added a delay for multi-reactions so that you don't get rate limited


## Usage

### Commands

| **Command**         | **Description**                                                                  |
| ------------------- | -------------------------------------------------------------------------------- |
| `react @user 😄👍`  | Starts auto-reacting to messages by a user with the specified emoji(s).          |                         
| `sr`                | Stops **all** active reactions and reacts with ✅ to your message.                |
| `wi <@user or ID>`  | Displays info about a user including permissions, join date, etc.                |
| `si`                | Shows server info like name, owner, member count, roles, channels, etc.          |
| `dw`                | Deletes previous output messages from `wi` or `si` and reacts with ✅.            |
| `av <@user or ID>`  | Sends the **global profile picture** of the user in 500x500 resolution.          |
| `sav <@user or ID>` | Sends the **server-specific profile picture** (supports GIFs if set) in 500x500. |
| `gif`               | Converts the latest attached or replied image to a GIF and sends it.             |
| `quit`              | Prompts confirmation and shuts down the selfbot if confirmed.                    |



## Installation

Install Python 3.12.4 (or any version after that)
Make sure to check the box that says "Add Python to PATH" during installation.

Open command prompt and type `git clone https://github.com/your-username/reactbot.git` then `cd reactbot` and `pip install -r requirements.txt`

Once you have done that, press Windows Key and R at the same time and type `%USERPROFILE%/ReactBot`

Open the ENV file in any text editor and place the token in the area of the code that says ```TOKEN = "YOUR_USER_TOKEN_HERE"``` and then run the reactbot
