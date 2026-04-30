import random

def select_misspellings_based_on_names(name_usage, note_resident, alternative_resident_redacted):
    """
    If a nickname is being used, don't allow misspellings 
    - it's clear that the name being used is not the one on record, so no need to introduce further ambiguity with misspellings. 
    If no name is being used, then set misspelt to None to avoid confusion
    """
    name_type = name_usage.get("type")
    # don't misspell if we're using a name different to the one on record
    if name_type == "nickname":
        misspelt = False
    # nothing to misspell if we're not using a name at all
    elif name_type == "none" or (note_resident =="alternative" and alternative_resident_redacted):
        misspelt = None
    # otherwise, allow ST to choose
    else:
        misspelt = name_usage.get("misspelt")
    
    return misspelt

def select_pronouns_based_on_name_usage(name_usage):
    """
    If the name type is "last_title", always use the correct pronouns.
    Otherwise, use the pronoun usage specified in the name usage.
    """
    name_type = name_usage.get("type")
    if name_type == "last_title":
        pronoun_usage = "correct"
    else:
        pronoun_usage = name_usage.get("pronounUsage")
    
    return pronoun_usage

def select_name_type_based_on_preferred_name(name_usage, note_resident, preferred_name):
    """
    If the name type is "preferred" but no preferred name is available and the note resident is the target,
    default to using the first name. Otherwise, use the specified name type.
    """
    name_type = name_usage.get("type")
    if name_type == "preferred" and preferred_name is None and note_resident == "target":
        return "first"
    else:
        return name_type

def clean_name_usage(params):
    """
    Cleans the name usage parameters by selecting the appropriate misspelling, pronoun usage,
    and name type based on the provided parameters.
    """
    name_usage = params["args"]["nameUsage"]
    note_resident = params["args"]["noteScenario"]["noteResident"]
    alternative_resident_redacted = params["args"]["alternativeResidentRedacted"]
    preferred_name = params["args"]["targetResident"]["preferredName"]

    name_usage["misspelt"] = select_misspellings_based_on_names(name_usage, note_resident, alternative_resident_redacted)
    name_usage["pronounUsage"] = select_pronouns_based_on_name_usage(name_usage)
    name_usage["type"] = select_name_type_based_on_preferred_name(name_usage, note_resident, preferred_name)

    return {
        "value": name_usage
    }

def redact_additional_resident(params):
    """
    Redacts the alternative resident's name if specified in the parameters.
    """
    redact = params["args"].get("alternativeResidentRedacted")
    alternative_resident = params["args"].get("alternativeResident")
    if redact:
        alternative_resident = "[REDACTED_PERSON_NAME_1]"
    
    return {
        "value": alternative_resident
    }