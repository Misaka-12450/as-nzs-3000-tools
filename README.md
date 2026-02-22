# AS/NZS 3000 Tools

A set of tools for calculations relating to AS/NZS 3000 (Wiring Rules), AS/NZS 3008 (Selection of Cables), related IEC rules, etc.

## Roadmap

### Standards

#### AS/NZS

- [x] AS/NZS 3000 Appendix C Table C1: Maximum Demand - Single and Multiple Domestic Electrical Installations

#### IEC

- [x] IEC 60898 Part 1 8.6 Table 7: Time-current operating characteristics

### Products

#### MCBs and RCBOs

- [x] Clipsal MAX9 RCBO trip curves
- [x] LS BKN MCB trip curves

## Set up

### 1. Docker

Docker images will be provided when this project is more substantial

### 2. Python virtual environment

1. Clone this repo:

   ```bash
   git clone https://github.com/Misaka-12450/as-nzs-3000-tools
   ```

2. Create a virtual environment using your favourite tool, such as [uv](https://docs.astral.sh/uv/getting-started/installation/):

   ```bash
   cd as-nzs-3000-tools
   uv venv .venv --python 3.13
   ```

3. Run the virtual environment depending on your platform:
   1. Windows

   ```powershell
   .venv\scripts\activate
   ```

   2. UNIX

   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies

   ```bash
   uv sync
   ```

5. Run Streamlit
   ```bash
   streamlit run streamlit_app.py
   ```

6. Visit the website at [http://localhost:8080](http://localhost:8080)
