# ET
![ET phone home](https://i.imgur.com/i2Y2d5y.jpg "ET phone home")

An opt-in system for gathering feedback on the usage of my scripts.

## Policy

This repository only holds code that can be used to send, receive, and record usage data.
Since it is just library code, it can actually be used any way the implementor desires.
But in my projects, I require the user to give explicit, well-informed consent before collecting any data.
For example, I give help text which explains that passing the `--phone-home` flag will send the following data to my server.

## The data

When a user runs one of my scripts with the `--phone-home` flag, it will make a connection to my server and send information on this invocation of the script.
The data sent is focused on getting a sense of how big the jobs are that people are using my code for, and how it performs on that data.
So if you're using one of my tools, I'd definitely appreciate the feedback!

Here is the full list of data which may be sent and recorded:

- IP address
  - This library assumes the server will log the IP making the connection to send the data.
- Timestamp
  - The same is true of the timestamp of when the connection is made.
- Project and command name
  - Which project of mine the tool is a part of, and the name of the script which was run.
- Version
  - The version of the script.
- Running time
  - How long the script took to run.
- CPU and memory usage
  - How much of these two resources the script used.
- Input size
  - The size of the input to the script. The format depends on the script. For example, it might be the size in bytes, the number of lines, or the number of sequencing reads.
- Whether the script was run as a Galaxy tool

My scripts will never send the input filenames or command line parameters, as useful as these might be in determining the source of performance problems.
I'm avoiding these data since they might give too much information on the type of study being performed. I'd also recommend being careful about sending things like exception details. These can also include filesystem paths which could identify the user. When my scripts include exception data, they do their best to remove this info before sending it.

Of course, the author of the particular script is responsible for what data is sent. There is a freeform JSON field which can include anything, so it's fully customizable.
