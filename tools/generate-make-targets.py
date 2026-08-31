#!/usr/bin/env python3

import re
from pathlib import Path


PLAYBOOKS_DIR = Path("playbooks")
MAKEFILE = Path("Makefile")
OUTPUT_FILE = Path("tools/generated-playbooks.mk")


def get_existing_targets(makefile: Path) -> set[str]:
    """Return targets already defined in Makefile."""
    targets = set()

    if not makefile.exists():
        return targets

    target_pattern = re.compile(r"^([^\s:#=]+)\s*(?::|!)")

    with makefile.open() as f:
        for line in f:
            # Ignore comments and indented lines
            if line.startswith((" ", "\t", "#")):
                continue

            match = target_pattern.match(line)
            if match:
                target = match.group(1)

                # Handle multiple targets:
                # foo bar: something
                targets.update(target.split())

    return targets


def main():
    existing_targets = get_existing_targets(MAKEFILE)

    playbooks = sorted(PLAYBOOKS_DIR.rglob("run-*.yml"))

    generated = 0
    skipped = 0

    with OUTPUT_FILE.open("w") as f:
        f.write("# This file is generated automatically.\n")
        f.write("# DO NOT EDIT MANUALLY.\n\n")

        for playbook in playbooks:
            # run-nginx.yml -> nginx
            target = playbook.stem.removeprefix("run-")

            if target in existing_targets:
                print(f"Skipping existing target: {target}")
                skipped += 1
                continue

            path = f"./{playbook.as_posix()}"

            f.write(f"{target}: prepare\n")
            f.write(f"\t$(call run_with_host,{path})\n\n")

            generated += 1

    print(
        f"Generated {generated} targets, "
        f"skipped {skipped} existing targets "
        f"in {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
