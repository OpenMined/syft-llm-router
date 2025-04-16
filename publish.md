## Publish Your Router

To make your router available to other users through your datasite's public folder, follow these steps:

1. Ensure your project has the following structure:
   - `router.py` - Your router implementation
   - `server.py` - Server configuration
   - `pyproject.toml` - Project dependencies
   - `README.md` - Project documentation

2. Prepare your project metadata:
   - Write a clear description of your router
   - Add relevant tags (comma-separated)
   - Ensure your README.md is comprehensive

3. Publish your router using the CLI:
```bash
uv run syftllm publish \
    --folder /path/to/your/router/project \
    --description "Your router description" \
    --tags "llm,phi-4,openrouter" \
    --readme README.md \
    --client-config /path/to/your/syft/config.json
```

Required parameters:
- `--folder`: Path to your router project directory
- `--description`: A clear description of your router
- `--tags`: Comma-separated list of relevant tags
- `--readme`: Path to your README.md file

Optional parameters:
- `--client-config`: Path to your Syft client configuration file

4. Verify the publication:
   - The CLI will validate your project structure
   - It will check for required files
   - It will generate and publish the metadata
   - You'll receive a success message if everything works

5. After successful publication:
   - Your router will be available in your datasite's public folder
   - Other users can discover and use your router
   - The metadata will include your documentation and endpoints

Note: Make sure your router implementation is stable and well-tested before publishing.

## Discovering Published Models

To discover and interact with published models, you can use the discover app. For detailed instructions on setting up and using the discover app, please refer to the [Discover App README](../discover/ReadME.md).

The discover app provides a web interface to:
- Browse all published models
- Search and filter models by tags and datasites
- View detailed model information and documentation
- Access model endpoints
