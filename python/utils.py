import random

def select_misspellings_based_on_names(name_usage, note_resident, alternative_resident_redacted):
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
    name_type = name_usage.get("type")
    if name_type == "last_title":
        pronoun_usage = "correct"
    else:
        pronoun_usage = name_usage.get("pronounUsage")
    
    return pronoun_usage

def clean_name_usage(params):
    name_usage = params["args"]["nameUsage"]
    note_resident = params["args"]["noteScenario"]["noteResident"]
    alternative_resident_redacted = params["args"]["alternativeResidentRedacted"]

    name_usage["misspelt"] = select_misspellings_based_on_names(name_usage, note_resident, alternative_resident_redacted)
    name_usage["pronounUsage"] = select_pronouns_based_on_name_usage(name_usage)
    return {
        "value": name_usage
    }

def redact_additional_resident(params):
    redact = params["args"].get("alternativeResidentRedacted")
    alternative_resident = params["args"].get("alternativeResident")
    if redact:
        alternative_resident = "[REDACTED_PERSON_NAME_1]"
    
    return {
        "value": alternative_resident
    }