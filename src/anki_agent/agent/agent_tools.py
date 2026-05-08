"""Agent Tools for Anki Note Creation and Export

Tools for creating Anki plaintext export files from structured note data. Includes functions for
normalizing field values, formatting tags, building export headers, and creating various note types
(Basic, Cloze, Image Occlusion). The main export function writes a list of note dictionaries to a
tab-delimited plaintext file that can be imported into Anki.
"""

from strands import tool


def normalize_anki_field(field_value: str) -> str:
    """Normalize a field value for Anki plaintext export by replacing newlines and tabs with spaces,
    and removing carriage returns. The tabs are still important between empty fields to ensure the
    correct number of columns, but any tabs within field values should be replaced with spaces to
    avoid formatting issues.

    Args:
        field_value (str):  The original field value, which may contain newlines, tabs, or carriage
                            returns.

    Returns:
        str: The normalized field value with newlines and tabs replaced by spaces, and carriage
             returns removed.
    """
    if (field_value is None):
        return ""

    text = str(field_value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    return text


def format_tags(tags: (list[str] | None)) -> str:
    """Format a list of tags for Anki plaintext export by stripping whitespace and joining with
    spaces. Different tags are separated simply by spaces in Anki, while subtags can be created by
    using "::" within a single tag (e.g., "tag::sub-tag"). These can be chained to create multiple
    levels of subtags, but it is best practice to be conservative and consistent.

    Args:
        tags (list[str]  |  None): The list of tags to format. If None or empty, an empty string
                                   will be returned.

    Returns:
        str: The formatted tags string.
    """
    if (not tags):
        return ""
    
    return " ".join(str(tag).strip() for tag in tags if str(tag).strip())


@tool
def build_anki_export_header(html: bool = True) -> str:
    """Build the standard header for an Anki plaintext export file. Guid columns are excluded from
    column 1, as they are not necessary for Anki to import the notes correctly, and can cause issues
    with some versions of Anki. The header includes directives for the separator character, whether
    HTML is included in the export, and which columns correspond to the note type, deck, and tags.
    If the "html" parameter is set to False, then the fielld values should NOT invlude any HTML
    formatting and or tags.

    Args:
        html (bool, optional): Whether to include HTML in the export. Default to True.

    Returns:
        str: The formatted header string for the Anki plaintext export file.
    """
    return "\n".join(
        [
            "#separator:tab",
            f"#html:{'true' if html else 'false'}",
            f"#notetype column:1",
            f"#deck column:2",
            f"#tags column:8"
        ]
    )


@tool
def format_anki_export_row(
    note_type: str,
    deck: str,
    fields: list[str],
    tags: (list[str] | None) = None
) -> str:
    """Format a single Anki plaintext export row for a note. This will sanitize field values, format
    tags, and join all values with tabs to create a single export row string.

    Args:
        note_type (str): The note type (e.g., "Basic", "Cloze").
        deck (str): The deck to which the note belongs.
        fields (list[str]): The list of field values for the note.
        tags (list[str] | None, optional): The list of tags for the note. Defaults to None.

    Returns:
        str: The formatted export row.
    """
    safe_fields = [normalize_anki_field(field) for field in fields]

    if safe_fields.__len__() < 5:
        safe_fields += [""] * (5 - safe_fields.__len__())
        
    tag_value = format_tags(tags)
    return "\t".join(
        [
            note_type,
            deck,
            *safe_fields,
            tag_value
        ]
    )


@tool
def build_anki_note(
    note_type: str,
    deck: str,
    fields: list[str],
    tags: (list[str] | None) = None
) -> dict:
    """Create a generic Anki note payload that can be serialized to plaintext.

    Args:
        note_type (str): The note type (e.g., "Basic", "Cloze").
        deck (str): The deck to which the note belongs.
        fields (list[str]): The list of field values for the note.
        tags (list[str] | None, optional): The list of tags for the note. Defaults to None.

    Returns:
        dict: The formatted Anki note payload.
    """
    return {
        "note_type": note_type,
        "deck": deck,
        "fields": fields,
        "tags": tags
    }


@tool
def create_basic_note(
    deck: str = "Default",
    front: str = "",
    back: str = "",
    tags: (list[str] | None) = None
) -> dict:
    """Create a Basic note payload for an Anki plaintext export. This note type is best for
    question-answer pairs, where the "front" field contains the question or prompt, and the "back"
    field contains the answer or response.

    Args:
        deck (str, optional): The deck to which the note belongs. Defaults to "Default".
        front (str, optional): The front field of the note. Defaults to "".
        back (str, optional): The back field of the note. Defaults to "".
        tags (list[str] | None, optional): The list of tags for the note. Defaults to None.

    Returns:
        dict: The formatted Basic note payload.
    """
    return build_anki_note(
        "Basic",
        deck,
        [front, back],
        tags
    )


@tool
def create_basic_reversed_note(
    deck: str = "Default",
    front: str = "",
    back: str = "",
    tags: (list[str] | None) = None
) -> dict:
    """Create a Basic (and reversed card) note payload for an Anki plaintext export. This note type
    is best for headword-definition pairs, synonym pairs, or any other type of information where it
    would be beneficial to have two cards generated and studied both ways. Because of this, using
    question-answer pairs with this note type is not recommended.

    Args:
        deck (str, optional): The deck to which the note belongs. Defaults to "Default".
        front (str, optional): The front field of the note. Defaults to "".
        back (str, optional): The back field of the note. Defaults to "".
        tags (list[str] | None, optional): The list of tags for the note. Defaults to None.

    Returns:
        dict: The formatted Basic (and reversed card) note payload.
    """
    return build_anki_note(
        "Basic (and reversed card)",
        deck,
        [front, back],
        tags
    )


@tool
def create_basic_optional_reversed_note(
    deck: str = "Default",
    front: str = "",
    back: str = "",
    add_reverse: str = "",
    tags: (list[str] | None) = None
) -> dict:
    """Create a Basic (optional reversed card) note payload for an Anki plaintext export. This note
    type is best for headword-definition pairs, synonym pairs, or any other type of information
    where it would be beneficial to have two cards generated and studied both ways. Because of this,
    using question-answer pairs with this note type is not recommended. The "add_reverse" field can
    be used to provide additional information on the reverse card, such as further context or
    explication. The "back_extra" field is optional, and can be left as an empty string if no
    additional information is needed.
    
    Args:
        deck (str, optional): The deck to which the note belongs. Defaults to "Default".
        front (str, optional): The front field of the note. Defaults to "".
        back (str, optional): The back field of the note. Defaults to "".
        add_reverse (str, optional): The additional reverse field of the note. Defaults to "".
        tags (list[str] | None, optional): The list of tags for the note. Defaults to None.

    Returns:
        dict: The formatted Basic (optional reversed card) note payload.
    """
    return build_anki_note(
        "Basic (optional reversed card)",
        deck,
        [front, back, add_reverse],
        tags
    )


@tool
def create_cloze_note(
    deck: str = "Default",
    text: str = "",
    back_extra: str = "",
    tags: (list[str] | None) = None
) -> dict:
    """Create a Cloze note payload for an Anki plaintext export. This note type is best for
    fill-in-the-blank style questions, where the "text" field contains the full text with cloze
    deletions in the syntax of {{c1::answer}}, {{C2::answer2}}, {{C3::answer3 {{c4::answer4}}}},
    etc. The "back_extra" field contains any additional information that should be included with the
    answer on the back of the card. The "back_extra" field is optional, and can be left as an empty
    string if no additional information is needed beyond the cloze-deleted text.
    
    Args:
        deck (str, optional): The deck to which the note belongs. Defaults to "Default".
        text (str, optional): The text field of the note. Defaults to "".
        back_extra (str, optional): The additional back field of the note. Defaults to "".
        tags (list[str] | None, optional): The list of tags for the note. Defaults to None.

    Returns:
        dict: The formatted Cloze note payload.
    """
    return build_anki_note(
        "Cloze",
        deck,
        [text, back_extra],
        tags
    )


# @tool
def create_image_occlusion_note(
    deck: str = "Default",
    occlusion: str = "",
    image: str = "",
    header: str = "",
    back_extra: str = "",
    comments: str = "",
    tags: (list[str] | None) = None
) -> dict:
    """Create an Image Occlusion note payload for an Anki plaintext export. This note type is best
    for memorizing information on diagrams, charts, maps, or any other type of visual information.
    This tool is WIP, as it requires heavy html styling and specific formatting to work properly,
    and may not render correctly in its current state.

    Args:
        deck (str, optional): The deck to which the note belongs. Defaults to "Default".
        occlusion (str, optional): The occlusion field of the note. Defaults to "".
        image (str, optional): The image field of the note. Defaults to "".
        header (str, optional): The header field of the note. Defaults to "".
        back_extra (str, optional): The additional back field of the note. Defaults to "".
        comments (str, optional): The comments field of the note. Defaults to "".
        tags (list[str] | None, optional): The list of tags for the note. Defaults to None.

    Returns:
        dict: The formatted Image Occlusion note payload.
    """
    return build_anki_note(
        "Image Occlusion",
        deck,
        [occlusion, image, header, back_extra, comments],
        tags,
    )


@tool
def write_anki_notes_plaintext(file_path: str, notes: list[dict], html: bool = True) -> str:
    """Write a list of Anki note dictionaries to a plaintext export file.
    
    Args:
        file_path (str): The path to the output file.
        notes (list[dict]): The list of Anki note dictionaries.
        html (bool, optional): Whether to include HTML formatting. Defaults to True.

    Returns:
        str: The path to the output file.
    """
    header = build_anki_export_header(html)
    rows = [header]
    for note in notes:
        rows.append(
            format_anki_export_row(
                note["note_type"],
                note["deck"],
                note.get("fields", []),
                note.get("tags", []),
            )
        )

    content = ("\n".join(rows) + "\n")
    with open(file_path, "w", encoding="utf-8") as output_file:
        output_file.write(content)

    return file_path
