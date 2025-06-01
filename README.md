# Discord ReactBot SelfBot 🤖💬

A very simple SelfBot that allows auto reactions and has the ability to mass react with multiple emojis

> ⚠️ Be aware that you can get rate limited if you like reactbot multiple members, I added a delay for multi-reactions so that you don't get rate limited


## Usage

### Commands

- `react @username 😄`  
  Begins reacting to future messages from the mentioned user with the specified emojis.

- `stop react @username`  
  Stops reacting to that user's messages.

### Example

```txt
react @user 😄
stop react @user
```
## Installation

Install Python 3.12.0 (or any version after that)
Make sure to check the box that says "Add Python to PATH" during installation.

Once Python has been installed open a command prompt and type in
pip install discord.py-self==1.9.3

Download the reactbot.py
You will then need to find your token, there are plenty tutorials for this online

Place the token in the area of the code that says ```TOKEN = "YOUR_USER_TOKEN_HERE"``` and then run the reactbot
