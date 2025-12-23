import csv
import os
import re


def clean_class_name(name):
    # Remove source info like (PHB'24), (TCE), (XGE) and strip whitespace
    # We want to keep subclass info like (Arcane Trickster)
    name = re.sub(r"\s*\((PHB'24|TCE|XGE)\)", "", name).strip()
    return name


def parse_poziom(poziom):
    if "Sztuczka" in poziom:
        return 0
    match = re.search(r"(\d+)", poziom)
    if match:
        return int(match.group(1))
    return 0


def convert():
    input_file = "/home/ciszko/DnDHelp/Spells_PL.csv"
    output_dir = "/home/ciszko/DnDHelp/spells_md"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nazwa = row["Nazwa"]
            if not nazwa:
                continue

            poziom_raw = row["Poziom"]
            krag = parse_poziom(poziom_raw)

            szkola_raw = row["Szkoła"]
            rytual = "true" if "(rytuał)" in szkola_raw.lower() else "false"
            szkola = szkola_raw.replace("(rytuał)", "").strip()

            # Components
            komponenty_raw = row["Komponenty"].split(",")
            komponenty = []
            for k in komponenty_raw:
                k = k.strip()
                if k:
                    # Extract just the first letter (W, S, M) or keep as is?
                    # The example shows just the letters.
                    # But M often has details. Let's keep the letter for the list.
                    match = re.match(r"^([WSM])", k, re.I)
                    if match:
                        komponenty.append(match.group(1).upper())
                    else:
                        komponenty.append(k)

            # Classes
            klasy_combined = (
                row["Klasy"] + ", " + row["Opcjonalne klasy"] + ", " + row["Podklasy"]
            )
            klasy_raw = klasy_combined.split(",")
            klasy_set = set()
            for k in klasy_raw:
                cleaned = clean_class_name(k)
                if cleaned:
                    klasy_set.add(cleaned)
            klasy = sorted(list(klasy_set))

            # Description
            opis = row["Opis"]
            if row["Na wyższych poziomach"]:
                opis += "\n\n" + row["Na wyższych poziomach"]

            # Style refinements to match user example
            # Remove colons to avoid YAML parsing errors
            nazwa = nazwa.replace(":", "")

            czas_rzucania = row["Czas rzucania"]
            czas_rzucania = czas_rzucania.replace("Akcja", "1 akcja")
            czas_rzucania = czas_rzucania.replace("Dodatkowa", "1 akcja dodatkowa")
            czas_rzucania = czas_rzucania.replace("Reakcja", "1 reakcja")
            czas_rzucania = czas_rzucania.replace(":", "")

            zasieg = row["Zasięg"]
            zasieg = zasieg.replace(" m", " metrów")
            zasieg = zasieg.replace(" km", " kilometrów")
            zasieg = zasieg.replace(":", "")

            szkola = szkola.replace(":", "")

            # Create Markdown content
            md_content = "---\n"
            md_content += f"krąg: {krag}\n"
            md_content += f"nazwa: {nazwa}\n"
            md_content += f"szkoła: {szkola}\n"
            md_content += f"czas rzucania: {czas_rzucania}\n"
            md_content += f"zasięg: {zasieg}\n"

            md_content += "komponenty:\n"
            for k in komponenty:
                md_content += f"  - {k}\n"

            md_content += f"czas trwania: {row['Czas trwania']}\n"

            md_content += "klasa:\n"
            for k in klasy:
                md_content += f"  - {k}\n"

            md_content += f"rytuał: {rytual}\n"

            # Use |- for multiline string in YAML to preserve newlines
            md_content += "opis: |-\n"
            # Indent the description
            indented_opis = "  " + opis.replace("\n", "\n  ")
            md_content += indented_opis + "\n"

            md_content += "\n---"

            # Write to file
            filename = f"{nazwa}.md".replace("/", "-")  # Basic sanitization
            filepath = os.path.join(output_dir, filename)
            with open(filepath, mode="w", encoding="utf-8") as mdfile:
                mdfile.write(md_content)

    print(f"Conversion complete. Files saved in {output_dir}")


if __name__ == "__main__":
    convert()
