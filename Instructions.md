1. For every mcp server there must be the following directory structure and files
    for each tool, there must be a tool folder [tool-name]-mcp (e.g. nuclei-mcp)
    within each tool folder there must be the following files
    a) Dockerfile (see example_Dockerfile for reference. The indepdnent tool file should be simpler than this, but this provides a simple reference.)
    b) publish_to_hackerdogs.sh (see sample file example_publish_to_hackerdogs.sh for foundation): take --build --publish tags (and help) default is --help --build (builds only) --publish (publishes only)
    c) README.md with logo of Hacklerdogs https://hackerdogs.ai/images/logo.png descripting the build, deployment and usage steps
    d) mcp_server.py that is an mcp server wrapper over the tool with very descriptive tool. Must use fastmcp.
    e) Every tool must support stdio and http-streamable protocol. Port if configurable and has default that doesn't conflict with other tools in the repo. Maintain the list of tool and ports in the root README.md (Cannot use ports: 80, 8501-8510, 8000-8010, 9000-9010, and other well known ports of popular apps.)
    e) mcpServer.json file that will be used to install the mcpServer in Claude or Cursor. See example_mcpServer.json in the sample-file folder.
2. A docker-compose file that include installing and starting the file
3. test.sh to test the mcp server using the mcp client. 
4. Create progress.md in the folder to track the progress of each step.