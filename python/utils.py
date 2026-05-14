import random

def select_misspellings_based_on_names(name_usage, note_resident, alternative_resident):
    """
    If a nickname is being used, don't allow misspellings 
    - it's clear that the name being used is not the one on record, so no need to introduce further ambiguity with misspellings. 
    If no name is being used, then set misspelt to None to avoid confusion
    """
    alternative_resident_redacted = isinstance(alternative_resident, str) and "REDACTED" in alternative_resident
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
    # get generated data to be checked and tweak
    name_usage = params["args"]["nameUsage"]
    note_resident = params["args"]["noteScenario"]["noteResident"]
    alternative_resident = params["args"]["alternativeResident"]
    preferred_name = params["args"]["targetResident"]["preferredName"]

    # Use helper functions to determine the final values for misspelling, pronoun usage, and name type
    name_usage["misspelt"] = select_misspellings_based_on_names(name_usage, note_resident, alternative_resident)
    name_usage["pronounUsage"] = select_pronouns_based_on_name_usage(name_usage)
    name_usage["type"] = select_name_type_based_on_preferred_name(name_usage, note_resident, preferred_name)

    # Return tweaked name usage data
    return {
        "value": name_usage
    }

def name_noise_generator():
    """
    Randomly create room number noise to add to a name
    """
    name_space = random.choice(["", " ", " ", " "]) # more likely to have a space than not
    room_types = ["", "room", "rm"]
    punctuation = ["", " ", "-", "_"]
    additional_letters = ["", "S"]

    room_noise = name_space + random.choice(room_types) + random.choice(punctuation) + random.choice(additional_letters) + str(random.randint(1, 50))

    return room_noise

def clean_preferred_name(params):
    """
    Randomly sets the preferred name to the same as the first name
    Also randomly adds noise to the preferred name (simulated room number)
    Tests the program's ability to handle these instances
    """
    target_resident = params["args"]["targetResident"]
    first_name = target_resident["firstName"]
    preferred_name = target_resident["preferredName"]

    # Don't do anything if there's no preferred name
    if preferred_name is None:
        return {
            "value": target_resident
        }

    first_preferred_same = random.random() < 0.5  # 50% chance to set preferred name the same as first name
    if first_preferred_same:
        preferred_name = first_name

    # don't add noise here, this can confuse the LLM when generating care notes
    # add noise after having generated the care note
    # add_noise = random.random() < 0.7  # 70% chance to add noise
    # if add_noise:
    #     preferred_name = preferred_name + name_noise_generator()

    target_resident["preferredName"] = preferred_name

    return {
        "value": target_resident
    }