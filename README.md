# CyberCipher Project

I built a Startup Assistant that allows you to Brainstorm Ideas by generating agent experts to let you ideate from all possible viewpoints. It also consists of  SWAT analyzer as well as a LOGO Genrate which should capture the essence of your idea and startup. 

# Ideate

Here, when given a prompt, multiple agentic experts relevant to your idea or problem will be generated, assisting you to brainstrom and pitch solutions against your idea. The process is well demonstrated in the demo video. The agents created are listed on the sidebar, to identify the agents created (current implementation has fixed names, not dynamic). Each agent builds on the previous one's response.

This was implemented by using Microsoft's `Autogen` library that provides support for multi-agent conversations, `Gemini` as the LLM, and the communication was fetched on the frontend by using asynchronous calls.

It also allows you to create multiple chat options to brainstorm multiple ideas, while maintaining consistency when switching the context.

# SWAT Analyzer

We utilize LLM calls to generate the reviews, tools to fetch relevant resources and then postprocess the outputs to beatify the responses. This allows to have a quick review of your idea while also receiving suggestions and external resources to improve your idea.

# LOGO Generator

Every company is incomplete without a logo, which signifies the purpose and motivation of a company. We implemented this logo generator by utilizing `NVIDIA's Stable Diffusion API`.




*This was created at an 18-hour hackathon*
