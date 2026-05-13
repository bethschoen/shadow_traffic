# Data Creation with ShadowTraffic

## Problem Statement
As our reliance on LLMs to generate and transform unstructured text data grows, we must consider how to confidently evaluate the performance of the model. This is particularly important for tasks like classification where the output can inform business-critical decision making. 

LLMs were originally chosen to perform the task because they require no training, only a prompt, and are thus much faster to set-up. They don't require a labelled training dataset to understand the task. This is ideal for quick development and deployment, but poses a significant risk when the evaluating the output. **Without a labelled dataset, how do we know if the model is correct?**

One solution is to manually observe outputs as they are generated. While a human-in-the-loop is recommended, it can't be the only solution. Manual labelling is prone to human error and doesn't result in a large enough dataset. 

What if there was a way to simulate production data, its structure and patterns, and automatically and confidently label it?

## ShadowTraffic: Dummy Data Generation
This repo explores how to use ShadowTraffic to efficiently generate simulated data using instructions in JSON format:
1. Create a config that designs controlled scenarios, highlighting the key patterns the text data needs to capture
2. Parse each scenario to an LLM for text generation
3. Label the text data using the config values

This dataset can then be used to test the accuracy of the production model.

ShadowTraffic allows us to randomise names, booleans (`"misspelt": true`), select from lists (`"noteResident": "target"`). These features combined create the config required to set-up scenarios.

## Care Note Example
We're using LLMs to identify whether a care note has been saved to the correct patient:

<img alt="voided route logic" src="assets/st_voided_route.png" width=450/>

Therefore, our controlled, labelled dataset will need to include a variety of strings containing names - some being the target patient and others being random people. 

### Scenario Generation

We can control:
- The resident's and alternative person's identities (name, sex)
- Which name fragment was used for the resident. Is an unrecorded nickname used?
- Whether the note uses the expected pronouns (does it align with the patient's recorded sex)?
- Whether their name is spelt correctly?
- Additional names in the note. Is anyone else mentioned? In what capacity?

<img alt="fake voided data" src="assets/st_scenarios.png" width=500/>

We can create these fields using lines such as:

```json
"preferredName": {
    "_gen": "string", 
    "expr": "#{Name.firstName}", 
    "null": {
        "rate": 0.2
    }, 
    "locale": [
        "en", 
        "gb"
    ]
},
"sex": {
    "_gen": "oneOf", 
    "choices": [
        "Male", 
        "Female"
    ]
},
"misspelt": {
    "_gen": "weightedOneOf",
    "choices": [
        {
            "weight": 3,
            "value": true
        },
        {
            "weight": 7,
            "value": false
        }
    ]
}
```

An example output from our ShadowTraffic config looks like this:

```json
{
    "targetResident" : {
        "firstName" : "Moshe",
        "preferredName" : "Arthur",
        "lastName" : "Weissnat",
        "sex" : "Male"
    },
    "alternativeResident" : {
        "firstName" : "Shoshana",
        "lastName" : "Tillman",
        "sex" : "Male",
        "preferredName" : "Tyrell"
    },
    "noteScenario" : {
        "noteResident" : "alternative",
        "additionalNamesMentioned" : "Reed",
        "sentiment" : "neutral"
    },
    "nameUsage" : {
        "pronounUsage" : "non-binary",
        "type" : "first",
        "misspelt" : false
    }
  }
```

### Custom Functions

There were some combinations of config values that didn't make sense. For example, how can `nameUsage.type` be "preferred" if the target resident doesn't have a preferred name? Therefore, custom functions were introduced to manually tweak ShadowTraffic outputs that don't logically work together. 

Here's a function that tweaks values in the `nameUsage` section:

```python
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
```

Then in the config, the custom function is called along with variables generated by ShadowTraffic: 

```json
"nameUsage": {
    "_gen": "customFunction",
    "language": "python",
    "file": "/home/python/utils.py",
    "function": "clean_name_usage",
    "args": {
        "nameUsage": {
            "_gen": "var",
            "var": "nameUsage"
        },
        "noteScenario": {
            "_gen": "var",
            "var": "noteScenario"
        },
        "alternativeResident": {
            "_gen": "var",
            "var": "alternativeResident"
        },
        "targetResident": {
            "_gen": "var",
            "var": "targetResident"
        }
    }
}
```

### AI Text Generation

Any previous values generated by ShadowTraffic can be parsed alongside a prompt to an AI model. With Ollama set-up locally, this command is able to use the downloaded model `llama3.2:3b` (this model isn't very big, but my laptop also isn't very strong 🤷🏻‍♀️):

```json
"careNote": {
    "_gen":"ai",
    "service": "ollama",
    "ollama": {
        "url": "http://host.docker.internal:11434",
        "model": "llama3.2:3b",
        "prompt": {
            "_gen": "env",
            "var": "VOIDED_PROMPT"
        }
    }
}
```

The care note generation prompt is externalised from the ShadowTraffic config and supplied at runtime through an environment variable. As the prompt can be quite long, this makes it easier to maintain. It also removes large text from the config file. The two tasks/concerns are separated. The prompt includes instructions on how to use the provided values.

```md
...
# Instructions
- The note you create belongs to the individual assigned to `noteScenario.noteResident`: their health, status, or actions are part of the note's observation; they are a direct participant.
- Write a short care note (1-2 lines, may include shorthand or semi-structured phrases)
- Respect nameUsage rules (misspellings, pronouns, etc.)
- **Do NOT create any other names.** Only use the names that have been provided.
- If `"alternativeResident" == "[REDACTED_PERSON_NAME_1]"` and `"noteScenario.noteResident" == "alternative"`:
  - The resident's information has been redacted. Construct the note using the placeholder.
...
```

The example scenario above led to the following care note:

```json
{
    "careNote": "Mobility: needed a two handed hoist, Shoshana assisted with getting up. Happiness: OK."
}
```

To be honest, `llama3.2:3b` didn't do a fantastic job. It took an example from the prompt and replaced "resident" with "Shoshana". It didn't include the additional name. Larger, stronger models are available for handling complex tasks. 

We also parsed the scenarios to `Gemini-2.5-Flash` in GCP - the production model. It was able to produce care notes that matched the anticipated labels. Here's the above example again:

```json
{
    "careNote": "Shoshana had their morning tea in the lounge. They chatted briefly with Reed before returning to their room.",
    "expectedLabel": "INCORRECT",
    "expectedNames": [
        "Shoshana",
        "Reed"
    ]
}
```

**Choice of model has a big impact on success.**

## How to Use ShadowTraffic (Locally)
Here are the steps for using ShadowTraffic in an environment where Docker and Ollama have been installed, and a model has been downloaded for local use (see below additional notes on Ollama usage). 

### 1. Create license.env file
This is used for authentication and lives in the route directory.

### 2. Setup config and python files
Create the `.json` file that designs your data. Feel free to create any python files that can control/tweak your ShadowTraffic values as you please. My utils live in a dedicated python folder. 

### 3. Run
Here's the command I've been using to run my Voided data generator. In addition to the license and config files, I need to tell it where my python files live and where I want my output data to save locally (as I'm only saving to my local file system). I also need to create an environment variable specifying my prompt. I opted to created my variable using `export` as the prompt is super long and contains new line characters. The variable will available for the session only (it doesn't persist).

```bash
export VOIDED_PROMPT="$(cat prompts/voided_prompt.txt)"

echo "$VOIDED_PROMPT" | head

docker run \
  --env-file "$(pwd)/license.env" \
  -v "$(pwd)/configs/voided.json:/home/config.json" \
  -v "$(pwd)/output:/data" \
  -v "$(pwd)/python:/home/python" \
  -e VOIDED_PROMPT \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json
```

If we **don't** want to save the outputs anywhere and just view them, add the below commands (this will print 2 samples to the terminal).

```bash
--stdout --sample 2
```

## Ollama Side Note

This section has been added to remind me on how Ollama was set-up to work with LLMs locally. 

### 1. Install Ollama
I installed the desktop application via their website.

### 2. Choose an LLM
Their website lists all the models you have available. Remember to consider the number of parameters! Some of these models are huuuuuuge. 

### 3. Download LLM
To download a chosen LLM, run in the terminal `ollama run <model name>`. 

### 4. Test it's working
Once the model has been download, you’ll see a prompt like:
`>>> `

You can type:
```bash
Write a haiku about residental care homes. 
```

If it responds sensibly, everything is working.

Exit with:
```bash
/bye
```

### 5. Specify model in the config
Include the exact name of the model in your config.json file. 

### 6. Remove the model when you're done 
Run `ollama rm <model name>` to delete the model when you no longer need it. 