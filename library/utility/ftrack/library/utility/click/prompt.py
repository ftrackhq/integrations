# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click

from typing import Any, List


# Simple helper function to prompt for a choice from a list of valid options.
def prompt_for_choice(
    options: List[str], user_input: Any, prompt_label: str, allow_custom: bool = False
) -> str:
    """
    Prompts the user to select a valid option from a given list of options.

    :param options: The list of valid options (strings)
    :param user_input: The user input (if provided)
    :param prompt_label: A label for the prompt, e.g. "version", "variant"
    :param allow_custom: If True, the user can manually type a value not in `options`.
    :return: The selected (or user-entered) option.
    """
    # If user_input is already valid, return it
    if user_input in options:
        return user_input

    # If user_input is provided but not valid, or not provided at all, show menu
    if user_input not in options:
        click.echo(f"Invalid {prompt_label} '{user_input}'")
    click.echo(f"Available {prompt_label}s:")
    for idx, opt in enumerate(options, start=1):
        click.echo(f"{idx}. {opt}")

    if allow_custom:
        click.echo(
            "Enter the number of the desired choice or type a custom value "
            f"(not in {prompt_label} list)."
        )
        choice_str = click.prompt("Enter a number or type a custom value", type=str)
        # If the user typed a number, try to interpret it
        if choice_str.isdigit():
            choice_idx = int(choice_str)
            if 1 <= choice_idx <= len(options):
                return options[choice_idx - 1]
            else:
                # They entered an out-of-range digit, treat it as custom
                return choice_str
        else:
            # It's not a digit, treat as custom value
            return choice_str
    else:
        # No custom allowed, prompt for integer
        choice = click.prompt(
            f"Enter the number of the {prompt_label} you want to use",
            type=click.IntRange(1, len(options)),
        )
        return options[choice - 1]
