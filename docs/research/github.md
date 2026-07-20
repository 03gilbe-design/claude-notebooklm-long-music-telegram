Here is a curated list of tools and repositories for generating animated architecture and data-flow diagrams, ranging from declarative languages to programmatic video engines:

1. **terrastruct/d2** 
   - **Stars:** ~18k
   - **What it does:** A declarative text-to-diagram language that natively supports animating connections (`animated: true`) and transitioning between different states/boards to visualize data flow.
   - **Output Format:** Animated SVG

2. **motion-canvas/motion-canvas**
   - **Stars:** ~17k
   - **What it does:** A TypeScript library specifically designed for creating programmatic, code-driven animations. It provides a specialized editor and timeline, making it perfect for explaining complex technical architectures and system flows.
   - **Output Format:** MP4, WebM, Image Sequences (GIF)

3. **magjac/d3-graphviz**
   - **Stars:** ~2.4k
   - **What it does:** Renders Graphviz DOT diagrams using D3.js. Its standout feature is smoothly interpolating and animating transitions between different graph states (e.g., nodes moving, edges changing).
   - **Output Format:** SVG DOM (can be screen-recorded/scripted to GIF)

4. **ManimCommunity/manim**
   - **Stars:** ~23k
   - **What it does:** A powerful Python engine for precise programmatic animations. Originally built for math (3Blue1Brown), developers frequently use it to script highly customized, fluid data-flow and microservice architecture animations.
   - **Output Format:** MP4, GIF

5. **remotion-dev/remotion**
   - **Stars:** ~19k
   - **What it does:** A framework for creating videos programmatically using React. Highly flexible for coding animated diagram components (like moving data packets along paths) and compiling them directly into videos.
   - **Output Format:** MP4, WebM

6. **jgraph/drawio**
   - **Stars:** ~39k
   - **What it does:** While a standard visual diagramming tool, it includes a specific "Flow Animation" property for connector edges that natively simulates data packets moving across your architecture.
   - **Output Format:** Animated SVG

7. **ryanhaining/GraphvizAnim**
   - **Stars:** ~150
   - **What it does:** A niche, proof-of-concept tool that automates the generation of Graphviz animations. You provide a base graph and a series of state changes, and it stitches the frames together.
   - **Output Format:** GIF, MP4

8. **mingrammer/diagrams**
   - **Stars:** ~37k
   - **What it does:** "Diagram as Code" for cloud architectures using Python. While it doesn't animate natively, developers use it programmatically to iterate through system states, generating sequences of frames to stitch into an animation.
   - **Output Format:** PNG sequences (requires external stitching to GIF)

9. **svgdotjs/svg.js**
   - **Stars:** ~10k
   - **What it does:** A lightweight JavaScript library for manipulating and animating SVGs. Often used by developers to take static SVG architectures (exported from Figma/Draw.io) and animate paths (stroke-dasharray) to show data flowing.
   - **Output Format:** Animated SVG DOM
