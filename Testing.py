import re
import requests
from bs4 import BeautifulSoup

def print_grid_from_doc(url):
    """
    Retrieves the document from the given URL, extracts its text content (using BeautifulSoup
    if necessary), filters out extra header/script lines, and then processes the remaining lines
    in groups of three (x-coordinate, character, y-coordinate).

    The x- and y-coordinates must be valid integers (matching the regex pattern),
    and the character line must be exactly one character long.
    Positions not specified will be filled with a space.
    The grid is printed with (0,0) at the top-left.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print("Error retrieving document:", e)
        return

    content = response.text

    # If the content looks like HTML, extract text with BeautifulSoup.
    if "<html" in content.lower():
        soup = BeautifulSoup(content, "html.parser")
        content = soup.get_text(separator="\n")
    
    # Split the text into lines.
    lines = content.splitlines()
    
    # Define a regex for an integer line and keywords for header lines.
    int_pattern = re.compile(r"^-?\d+$")
    header_keywords = ["coordinate", "character", "updated automatically", 
                       "coding assessment", "input data"]
    
    def is_code_line(line):
        lower = line.lower()
        return (line.startswith("var ") or line.startswith("function ") or
                line.startswith("<") or line.startswith("</") or
                "document." in lower or "window." in lower)

    records = []
    state = 0  # 0: expecting x-coordinate; 1: expecting character; 2: expecting y-coordinate
    temp_record = {}

    for line in lines:
        stripped = line.strip()
        # Skip blank lines, header lines, or lines that appear to be code.
        if (not stripped or 
            any(keyword in stripped.lower() for keyword in header_keywords) or 
            is_code_line(stripped)):
            continue

        if state == 0:
            # Expect an integer x-coordinate.
            if int_pattern.match(stripped):
                try:
                    temp_record["x"] = int(stripped)
                    state = 1
                except ValueError:
                    continue
            else:
                continue
        elif state == 1:
            # Expect a single character.
            if len(stripped) == 1:
                temp_record["char"] = stripped
                state = 2
            else:
                # If not valid, reset.
                state = 0
                temp_record = {}
        elif state == 2:
            # Expect an integer y-coordinate.
            if int_pattern.match(stripped):
                try:
                    temp_record["y"] = int(stripped)
                    records.append((temp_record["x"], temp_record["char"], temp_record["y"]))
                except ValueError:
                    pass
            # Reset state regardless.
            state = 0
            temp_record = {}

    if records:
        print("Found valid records:")
        for rec in records:
            print(rec)
    else:
        print("No valid records found.")
        return

    # Corrected: max_x from first element, max_y from third element of each record.
    max_x = max(int(x) for x, _, _ in records)
    max_y = max(int(y) for _, _, y in records)

    # Create grid with (0,0) at the top-left.
    grid = [[' ' for _ in range(max_x + 1)] for _ in range(max_y + 1)]
    for x, char, y in records:
        grid[int(y)][int(x)] = char

    # Print the grid row by row.
    for row in grid:
        print("".join(row))



url = "https://docs.google.com/document/d/e/2PACX-1vQGUck9HIFCyezsrBSnmENk5ieJuYwpt7YHYEzeNJkIb9OSDdx-ov2nRNReKQyey-cwJOoEKUhLmN9z/pub?output=txt"
print_grid_from_doc(url)
