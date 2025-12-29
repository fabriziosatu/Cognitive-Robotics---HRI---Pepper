# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from .utils import Utils

import logging
import os
import json
from .customer_tracking_system import TrackingPeople, TrackingGroups

script_dir = os.path.dirname(os.path.abspath(__file__))
FILE_PATH_DATABASE = os.path.join(script_dir, "database.json")
FILE_PATH_RANKING = os.path.join(script_dir, "ranking.json")

LINE_1 = "alpha line"
LINE_2 = "beta line"
LINE_3 = "gamma line"
LINE_4 = "delta line"

logging.getLogger(__name__)

# ====================================================
#  Class: ActionCountPeople(Action)
# ====================================================
class ActionCountPeople(Action):
    """
    Custom action for counting and providing information about people based on specified criteria.

    This action is designed to count and provide information about people passing through designate lines
    in a customer tracking system. It utilizes the TrackingPeople class for data processing.

    Global Attributes:
    - FILE_PATH_DATABASE (str): The file path to the JSON data containing information about people.
    - LINE_1 (str): The identifier for the first(alpha) line.
    - LINE_2 (str): The identifier for the second(beta) line.
    - LINE_3 (str): The identifier for the third(gamma) line.
    - LINE_4 (str): The identifier for the fourt(delta) line.

    Methods:
    - name(self) -> Text: Returns the name of the action ("action_count_people").
    - run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    Executes the action, counts people based on specified criteria, and provides relevant information.
    """
    
    def name(self) -> Text:
        """
        Returns the name of the action.

        Returns:
        - Text: The name of the action ("action_count_people").
        """
        return "action_count_people"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Executes the action, counts and provides the number of people who fulfil certain criteria set by the user.

        Parameters:
        - dispatcher (CollectingDispatcher): The dispatcher to send messages to the user.
        - tracker (Tracker): The conversation tracker containing user input history.
        - domain (Dict[Text, Any]): The domain configuration for the assistant.

        """

        # Extract current entities from the tracker
        entities = tracker.latest_message.get('entities')
        current_slots = tracker.current_slot_values()

        # Initialize the TrackingPeople
        cp = TrackingPeople(FILE_PATH_DATABASE, LINE_1, LINE_2, LINE_3, LINE_4, dispatcher, entities)
        for key, value in current_slots.items():
            if key in cp.foi:
                if value is not None and isinstance(value, list):
                    cp.foi[key] = tuple(value)
                else: 
                    cp.foi[key] = value if value != "None" else None
                    
        # Update the field of interest
        if cp.update() is True:
            # Get the data of interest - that is, the list of people that meet the required specifications.
            doi = cp.filteringJSON()

            dispatcher.utter_message(text=str(cp))
                
        return [
            SlotSet(key, value) 
            for key, value in cp.foi.items()
        ]

# ====================================================
#  Class: ActionReset(Action)
# ====================================================
class ActionReset(Action):

    def name(self) -> Text:
        return "action_reset"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            # Reset all slots
            return [AllSlotsReset()]


# ====================================================
#  Class: ActionsSlotMapping(Action)
# ====================================================
class ActionSlotMapping(Action):
    '''
    Custom action for mapping and updating slots based on recognized entities.
    '''

    def name(self) -> Text:
        """
        Returns the name of the action.

        Returns:
        - Text: The name of the action ("action_slot_mapping").
        """
        return "action_slot_mapping"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Executes the action, maps and updates slots based on recognized entities.

        Parameters:
        - dispatcher (CollectingDispatcher): The dispatcher to send messages to the user.
        - tracker (Tracker): The conversation tracker containing user input history.
        - domain (Dict[Text, Any]): The domain configuration for the assistant.

        Returns:
        - List[Dict[Text, Any]]: The list of events to be processed by the dialogue engine.
        """
        
        current_group: Dict[Text, Any] = dict()

        # Reset Slots if intent is 'finding_someone'
        if tracker.get_intent_of_latest_message() == 'finding_someone':
            new_slot_values = {key: None for key in tracker.current_slot_values().keys()}      
        else:
            new_slot_values = {key: value for key, value in tracker.current_slot_values().items()}      

        # Extract Entities
        entities = tracker.latest_message.get('entities')
        
        for entity in entities:

            entity_key = entity['entity']
            entity_value = entity['value']

            current_group[entity_key] = entity_value
                        
            # Update Clothing Fields
            if "clothing" in entity_key:
                neg = not "negation" in current_group
                
                current_group.clear()
                
                if entity_value in ["hat", "bag"]:
                    new_slot_values[entity_value] = neg
            
            # Update Gender Field    
            if "gender" in entity_key:
                neg = not "negation" in current_group
                current_group.clear()
                new_slot_values["gender"] = entity_value if neg is True else "female" if entity_value == "male" and neg is False else "male"
        
        return [
            SlotSet(key, value) 
            for key, value in new_slot_values.items()
        ]

# ====================================================
#  Class: ActionSubmit(Action)
# ====================================================
class ActionSubmit(Action):

    def name(self) -> Text:
        return "action_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            # Initialize the TrackingPeople
            cp = TrackingPeople(FILE_PATH_DATABASE, LINE_1, LINE_2, LINE_3, LINE_4, dispatcher)
            
            # Extract current slot values from the tracker and update corresponding fields in TrackingPeople
            current_slots = tracker.current_slot_values()
            for key, value in current_slots.items():
                if key in cp.foi:
                    cp.foi[key] = value if value != "None" else None
            
            # Filter JSON data based on the specified criteria (fields of interest)
            doi = cp.filteringJSON()
            output_string = ""
            # Check if there are filtered people
            if cp.nop != 0:
                # Iterate through filtered people and construct output string
                for i, field in enumerate(doi):
                    if cp.nop == 1:
                        gender_string = " He " if field["gender"] == "male" else " She " 
                    elif cp.nop > 1:
                        gender_string = f" The person number {i+1} "
                    else: 
                        dispatcher.utter_message("I encountered problems. Can you formulate your question better?")
                        return[AllSlotsReset()]
                    # Convert line passages to string format
                    line1_passages_string = ""
                    line1_passages_string = "once" if field["line1_passages"] == 1 else "twice" if field["line1_passages"] == 2 else f'{field["line1_passages"]} times'
                    line2_passages_string = ""
                    line2_passages_string = "once" if field["line2_passages"] == 1 else "twice" if field["line2_passages"] == 2 else f'{field["line2_passages"]} times'
                    line3_passages_string = ""
                    line3_passages_string = "once" if field["line3_passages"] == 1 else "twice" if field["line3_passages"] == 2 else f'{field["line3_passages"]} times'
                    line4_passages_string = ""
                    line4_passages_string = "once" if field["line4_passages"] == 1 else "twice" if field["line4_passages"] == 2 else f'{field["line4_passages"]} times'
                    # Construct the final output string
                    output_string += gender_string + f"crossed the alpha line {line1_passages_string}, the beta line {line2_passages_string}, the gamma line {line3_passages_string} and the delta line {line4_passages_string}."
                # Send the constructed message to the user
                dispatcher.utter_message(str(cp) + output_string)
            else:
                # If no people are found, send an appropriate message to the user
                dispatcher.utter_message("I'm sorry. " + str(cp) + " I can assist you by calling the mall security. They will be here in a few seconds.")
            
            # Reset all slots after processing
            return [AllSlotsReset()]
        
# ====================================================
#  Class: ValidateFindPersonForm(FormValidationAction) 
# ====================================================
class ValidateFindPersonForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_find_person_form"

    def validate_gender(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        if tracker.get_intent_of_latest_message() != "doubt" and slot_value is not None:
            if slot_value.lower() in ['male', 'm']:
                return {"gender": "male"}
            elif slot_value.lower() in ['female', 'f']:
                return {"gender": "female"}
            else:
                dispatcher.utter_message(text="Please provide a valid gender (male/female).")
                return {"gender": None}
        elif tracker.get_intent_of_latest_message() == "doubt":
            dispatcher.utter_message(text="It would help me a lot if you would tell me the gender.")
            return {"gender": None} 
        else:
            return {"gender": None}
        
    def validate_bag(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:        

        if slot_value is not None:
            if slot_value is not None and isinstance(slot_value, bool):
                return {"bag": True if slot_value is True else False}
            elif tracker.get_intent_of_latest_message() == "doubt":
                dispatcher.utter_message(response="utter_doubt")
                return {"bag": "None"} 
            else:
                if tracker.get_intent_of_latest_message() != "inform":
                    dispatcher.utter_message(text="Please provide a valid response (yes/no).")
                return {"bag": None}
        else:
            return {"bag": None}

    def validate_hat(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        if slot_value is not None:
            if slot_value is not None and isinstance(slot_value, bool):
                return {"hat": True if slot_value is True else False}
            elif tracker.get_intent_of_latest_message() == "doubt":
                dispatcher.utter_message(response="utter_doubt")
                return {"hat": "None"} 
            else:
                if tracker.get_intent_of_latest_message() != "inform":
                    dispatcher.utter_message(text="Please provide a valid response (yes/no).")
                return {"hat": None}
        else:
            return {"hat": None}
        
# ====================================================
#  Class: ActionCountGroups(Action) 
# ====================================================
class ActionCountGroups(Action):
    """
    Custom action for counting the groups that partecipated in the Artificial Vision contest based on specified criteria.

    It utilizes the TrackingGroups class for data processing.

    Global Attributes:
    - FILE_PATH_RANKING (str): The file path to the JSON data containing information about contest

    Methods:
    - name(self) -> Text: Returns the name of the action ("action_count_groups").
    - run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    Executes the action, counts groups based on specified criteria, and provides relevant information.
    """
    
    def name(self) -> Text:
        """
        Returns the name of the action.

        Returns:
        - Text: The name of the action ("action_count_groups").
        """
        return "action_count_groups"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Executes the action, counts and provides the number groups which fulfil certain criteria set by the user.

        Parameters:
        - dispatcher (CollectingDispatcher): The dispatcher to send messages to the user.
        - tracker (Tracker): The conversation tracker containing user input history.
        - domain (Dict[Text, Any]): The domain configuration for the assistant.

        """

        # Extract current entities from the tracker
        entities = tracker.latest_message.get('entities')
        current_slots = tracker.current_slot_values()

        # Initialize the TrackingGroups
        cg = TrackingGroups(FILE_PATH_RANKING, dispatcher, entities)
        for key, value in current_slots.items():
            if key in cg.foi:
                if value is not None and isinstance(value, list):
                    cg.foi[key] = tuple(value)
                else: 
                    cg.foi[key] = value if value != "None" else None

        # Update the field of interest
        if cg.update() is True:
            # Get the data of interest
            doi = cg.filteringJSON()

            dispatcher.utter_message(text=str(cg))
                
        return [
            SlotSet(key, value) 
            for key, value in cg.foi.items()
        ]
        
# ====================================================
#  Class: ActionResetOldSlot(Action)
# ====================================================
class ActionResetOldSlot(Action):

    def name(self) -> Text:
        return "action_reset_old_slot"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        current_slots = tracker.current_slot_values()
        
        if (len(entities) == 0 and current_slots.get("last_updated") is None):
            return [SlotSet("last_updated", "zero")]

        if len(entities) == 0 and current_slots.get("last_updated") is not None:
            return []

        if len(entities) == 2 and any(entity.get("value") == "negation" for entity in entities) and any(entity.get("value") == "mark" for entity in entities):
            return []

        if len(entities) > 1:
            return [SlotSet("last_updated", "more than one")]
    
        updated_slot = None
        for entity in entities:
            if entity["entity"] == "position":
                updated_slot = "position"
            elif entity["entity"] == "group_ID":
                updated_slot = "group_ID"
            elif entity["entity"] == "member_group":
                updated_slot = "member_group"
            elif entity["entity"] == "mark":
                updated_slot = "score"

        if updated_slot:
            return [SlotSet("last_updated", updated_slot)]

        return [SlotSet("last_updated", "wrong entity")]
    
    
# ====================================================
#  Class: ActionClassification(Action)
# ====================================================
class ActionClassification(Action):

    def name(self) -> Text:
        return "action_classification"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:   
    
        current_slots = tracker.current_slot_values()
        
        # check the value of the last_updated slot
        if current_slots.get("last_updated") == "zero":
            dispatcher.utter_message(text="Sorry, I did not understand who or what I need to research on. Could you rephrase please?") 
            return []
        
        if current_slots.get("last_updated") == "more than one":
            dispatcher.utter_message(text="I am so sorry, I can only handle one detail at a time for this kind of question. Please stop the conversation, then rephrase. You might ask who achieved a particular position, or, what position was achieved by a particular member or group.") 
            return [SlotSet("member_group", None), SlotSet("position", None), SlotSet("group_ID", None)]
        
        if current_slots.get("last_updated") == "wrong entity":
            dispatcher.utter_message(text="You provided a wrong entity for this type of research. Please rephrase.") 
            return []       
    
        with open(FILE_PATH_RANKING, 'r') as f:
           data = json.load(f)
         
        # if the user refers to a position  
        if current_slots.get("last_updated") == "position":
            
            position = current_slots.get("position")
            matching_group = next((group for group in data["groups"] if group["position"] == position), None)
            
            # if the position is in the json file
            if matching_group:
                group_id = matching_group["id"]
                group_members = ", ".join(matching_group["group_members"])
                dispatcher.utter_message(text= f"The group {group_id}, whose members are {group_members}, ranked in the {position} position.")
                return []
            else:
                dispatcher.utter_message(text= f"There is no group or member group in the {position} position. The positions range from first to fourteenth.")
                return []

        # if the user refers to a group_ID
        if current_slots.get("last_updated") == "group_ID":
            
            group_id_value = current_slots.get("group_ID")
            group_id_value = Utils.word_to_number(group_id_value, dispatcher)
            
            # check if the group number is a valid number
            if group_id_value == None:
                return []

            matching_group = next((group for group in data["groups"] if group["id"] == group_id_value), None)
            
            # if the group number is in the json file
            if matching_group:
                position = matching_group["position"]
                dispatcher.utter_message(text= f"The group {group_id_value} reached the {position} position is the contest.")
                return []
            else:
                dispatcher.utter_message(text= f"The group {group_id_value} did not take part in the contest. The groups number that participated in the contest range from one to fifteen, excluding eleven.")
                return []

        # if the user refers to a member_group
        if current_slots.get("last_updated") == "member_group":
            
            member_group = current_slots.get("member_group")
            member_group_lower = member_group.lower()
            matching_group = next((group for group in data["groups"] if any(member_group_lower == member.lower() for member in group["group_members"])), None)
            
            # if the member group is in the json file
            if matching_group:
                position = matching_group["position"]
                dispatcher.utter_message(text= f"{member_group} and the other member of the group reached the {position} position is the contest.")
                return []
            else:
                dispatcher.utter_message(text= f"{member_group} did not take part in the contest. If you provided firstname-surname, please provide lastname-firstname to try a new search.")
                return []
            
        if current_slots.get("last_updated") == "score":
            
            score = current_slots.get("score")
            score = Utils.word_to_number(score, dispatcher)
            
            negation = current_slots.get("negation")
            
            # check if the group number is a valid number
            if score == None:
                return []

            if negation is None:
                matching_groups = [group for group in data["groups"] if group["score"] >= score]
            else:
                matching_groups = [group for group in data["groups"] if group["score"] < score]
            
            position_values = [", ".join(group["position"]) for group in matching_groups if "position" in group]
            position_string = ", ".join(position_values)
            string = "have at least a score of" if negation is None else "have a score less than"
            
            if position_string:
                message = f"The position that {string} {score} are: {position_string}."
            else:
                message = f"No position found with a score of {string} {score}."

            dispatcher.utter_message(text=message)
            
# ====================================================
#  Class: ActionHavePartecipated(Action)
# ====================================================
class ActionHavePartecipated(Action):

    def name(self) -> Text:
        return "action_have_partecipated"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:   
    
        current_slots = tracker.current_slot_values()
        
        # check the value of the last_updated slot
        if current_slots.get("last_updated") == "zero":
            dispatcher.utter_message(text="Sorry, I did not understand who or what I need to research on. Could you rephrase please?") 
            return []
        
        if current_slots.get("last_updated") == "more than one":
            dispatcher.utter_message(text="I am so sorry, I can only handle one detail at a time for this kind of question. Please stop the conversation, then rephrase the question by denoting only one group or one member.") 
            return [SlotSet("member_group", None), SlotSet("position", None), SlotSet("group_ID", None)]
        
        if current_slots.get("last_updated") == "wrong entity":
            dispatcher.utter_message(text="You provided a wrong entity for this type of research. Please rephrase.") 
            return []       
    
        with open(FILE_PATH_RANKING, 'r') as f:
           data = json.load(f)           

        # if the user refers to a group_id
        if current_slots.get("last_updated") == "group_ID":
            
            group_id_value = current_slots.get("group_ID")
            group_id_value = Utils.word_to_number(group_id_value, dispatcher)
            
            # check if the group number is a valid number
            if group_id_value == None:
                return []

            matching_group = next((group for group in data["groups"] if group["id"] == group_id_value), None)
            
            # if the group number is in the json file
            if matching_group:
                dispatcher.utter_message(text= f"Yes, the group {group_id_value} took part in the contest.")
                return []
            else:
                dispatcher.utter_message(text= f"No, the group {group_id_value} did not take part in the contest. The groups number that participated in the contest range from one to fifteen, excluding eleven.")
                return []

        # if the user refers to a member_group
        if current_slots.get("last_updated") == "member_group":
            
            member_group = current_slots.get("member_group")
            member_group_lower = member_group.lower()
            matching_group = next((group for group in data["groups"] if any(member_group_lower == member.lower() for member in group["group_members"])), None)
            
            # if the member group is in the json file
            if matching_group:
                dispatcher.utter_message(text= f"Yes, {member_group} took part in the contest.")
                return []
            else:
                dispatcher.utter_message(text= f"No, {member_group} did not take part in the contest. If you provided firstname-surname, please provide lastname-firstname to try a new search.")
                return []
            
        if current_slots.get("last_updated") == "position":
            dispatcher.utter_message(text= "I am sorry, I am not able to answer if a position has parecipated in the contest. Please stop the conversation, then rephrase.")
            return []
        
        if current_slots.get("last_updated") == "score":
            dispatcher.utter_message(text= "I am sorry, I am not able to answer if a score has parecipated in the contest. Please stop the conversation, then rephrase.")
            return []

# ====================================================
#  Class: ActionMembersGroup(Action)
# ====================================================
class ActionMembersGroup(Action):

    def name(self) -> Text:
        return "action_members_group"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:   
    
        current_slots = tracker.current_slot_values()
        
        # check the value of last_updated slot
        if current_slots.get("last_updated") == "zero":
            dispatcher.utter_message(text="Sorry, I did not understand who or what I need to research on. Could you rephrase please?") 
            return []
        
        if current_slots.get("last_updated") == "more than one":
            dispatcher.utter_message(text="I am so sorry, I can only handle one detail at a time for this kind of question. Please stop the conversation, then rephrase the question by denoting only one group or one member or one position.") 
            return [SlotSet("member_group", None), SlotSet("position", None), SlotSet("group_ID", None)]
        
        if current_slots.get("last_updated") == "wrong entity":
            dispatcher.utter_message(text="You provided a wrong entity for this type of research. Please rephrase.") 
            return []       
    
        with open(FILE_PATH_RANKING, 'r') as f:
           data = json.load(f)
         
        # if the user refers to a psotion
        if current_slots.get("last_updated") == "position":
            
            position = current_slots.get("position")
            matching_group = next((group for group in data["groups"] if group["position"] == position), None)
            
            # if the position is in the json file
            if matching_group:
                group_members = ", ".join(matching_group["group_members"])
                dispatcher.utter_message(text= f"The members of the group that ranked in the {position} position are: {group_members}.")
                return []
            else:
                dispatcher.utter_message(text= f"There is no members group in the {position} position. The positions range from first to fourteenth.")
                return []

        # if the user refers to a group_id
        if current_slots.get("last_updated") == "group_ID":
            
            group_id_value = current_slots.get("group_ID")
            group_id_value = Utils.word_to_number(group_id_value, dispatcher)
            
            # check if the group number is a valid number
            if group_id_value == None:
                return []

            matching_group = next((group for group in data["groups"] if group["id"] == group_id_value), None)
             
            # if the group number is in the json file
            if matching_group:
                group_members = ", ".join(matching_group["group_members"])
                dispatcher.utter_message(text= f"The members of group {group_id_value} are: {group_members}.")
                return []
            else:
                dispatcher.utter_message(text= f"The group {group_id_value} did not take part in the contest. The groups number that participated in the contest range from one to fifteen, excluding eleven.")
                return []

        # if the user refers to a member_group
        if current_slots.get("last_updated") == "member_group":
            
            member_group = current_slots.get("member_group")
            member_group_lower = member_group.lower()
            matching_group = next((group for group in data["groups"] if any(member_group_lower == member.lower() for member in group["group_members"])), None)
            
            # if the member group is in the json file
            if matching_group:
                matching_group["group_members"] = [member for member in matching_group["group_members"] if member.lower() != member_group_lower]
                group_members = ", ".join(matching_group["group_members"])
                dispatcher.utter_message(text= f"The temmates of {member_group} are: {group_members}.")
                return []
            else:
                dispatcher.utter_message(text= f"{member_group} did not take part in the contest. If you provided firstname-surname, please provide lastname-firstname to try a new search.")
                return []

        # if the user refers to a member_group
        if current_slots.get("last_updated") == "score":
            
            score = current_slots.get("score")
            score = Utils.word_to_number(score, dispatcher)
            
            negation = current_slots.get("negation")
            
            # check if the group number is a valid number
            if score == None:
                return []

            if negation is None:
                matching_groups = [group for group in data["groups"] if group["score"] >= score]
            else:
                matching_groups = [group for group in data["groups"] if group["score"] < score]
            
       
            members_group_values = [", ".join(group["group_members"]) for group in matching_groups if "group_members" in group]
            members_group_string = ", ".join(members_group_values)
            string = "of at least" if negation is None else "less than"
            
            if members_group_string:
                message = f"The members that have done a score {string} {score} are: {members_group_string}."
            else:
                message = f"No members found with a score {string} {score}."

            dispatcher.utter_message(text=message)
                
            return []
            
# ====================================================
#  Class: ActionGroupID(Action)
# ====================================================
class ActionGroupID(Action):

    def name(self) -> Text:
        return "action_group_id"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:   
    
        current_slots = tracker.current_slot_values()
        
        
        if current_slots.get("last_updated") == "more than one":
            dispatcher.utter_message(text="I am so sorry, I can only handle one detail at a time for this kind of question. Please stop the conversation, then rephrase the question by denoting only one member or one position.") 
            return [SlotSet("member_group", None), SlotSet("position", None), SlotSet("group_ID", None)]
        
        if current_slots.get("last_updated") == "wrong entity":
            dispatcher.utter_message(text="You provided a wrong entity for this type of research. Please rephrase.") 
            return []       
    
        with open(FILE_PATH_RANKING, 'r') as f:
           data = json.load(f)

        if current_slots.get("last_updated") == "zero":
            
            ids = [str(group["id"]) for group in data["groups"]]

            id_string = ",".join(ids)
            
            if id_string:
                dispatcher.utter_message(text= f"The groups that took part in the competition are: {id_string}.")
                return []
            
        # if the user refers to a position  
        if current_slots.get("last_updated") == "position":
            
            position = current_slots.get("position")
            matching_group = next((group for group in data["groups"] if group["position"] == position), None)
            
            # if the position is in the json file
            if matching_group:
                group_id = matching_group["id"]
                dispatcher.utter_message(text= f"The group {group_id} ranked in the {position} position.")
                return []
            else:
                dispatcher.utter_message(text= f"There is no group in the {position} position. The positions range from first to fourteenth.")
                return []
            
        # if the user refers to a member group
        if current_slots.get("last_updated") == "member_group":
            
            member_group = current_slots.get("member_group")
            member_group_lower = member_group.lower()
            matching_group = next((group for group in data["groups"] if any(member_group_lower == member.lower() for member in group["group_members"])), None)
            
            if matching_group:
                number = matching_group["id"]
                dispatcher.utter_message(text= f"Group {number} is the group that {member_group} is part of.")
                return []
            else:
                dispatcher.utter_message(text= f"{member_group} did not take part in the contest. If you provided firstname-surname, please provide lastname-firstname to try a new search.")
                return []

        if current_slots.get("last_updated") == "score":
            
            score = current_slots.get("score")
            if isinstance(score, list):
                score = score[0]
                score = str(score)
            score = Utils.word_to_number(score, dispatcher)
            
            negation = current_slots.get("negation")
            
            if score == None:
                return []

            if negation is None:
                matching_groups = [group for group in data["groups"] if group["score"] >= score]
            else:
                matching_groups = [group for group in data["groups"] if group["score"] < score]

            group_ids = [f"group {group['id']}" for group in matching_groups if "id" in group]

            group_ids_string = ", ".join(group_ids)
            string = "of at least" if negation is None else "less than"
            
            if group_ids_string:
                message = f"The groups that have done a score {string} {score} are: {group_ids_string}."
            else:
                message = f"No groups found with a score {string} {score}."

            dispatcher.utter_message(text=message) 
            return []

        if current_slots.get("last_updated") == "group_ID":
            dispatcher.utter_message(text= "I am sorry, you asked the number of the group when you already gave me this information. Please stop the conversation, then rephrase.")
            return []
    
            
# ====================================================
#  Class: ActionScoreDone(Action)
# ====================================================
class ActionScoreDone(Action):

    def name(self) -> Text:
        return "action_score_done"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:   
    
        current_slots = tracker.current_slot_values()
        
        # check the value of last_updated slot
        if current_slots.get("last_updated") == "zero":
            dispatcher.utter_message(text="Sorry, I did not understand who or what I need to research on. Could you rephrase please?") 
            return []
        
        if current_slots.get("last_updated") == "more than one":
            dispatcher.utter_message(text="I am so sorry, I can only handle one detail at a time for this kind of question. Please stop the conversation, then rephrase the question by denoting only one group or one member or one position.") 
            return [SlotSet("member_group", None), SlotSet("position", None), SlotSet("group_ID", None)]
        
        if current_slots.get("last_updated") == "wrong entity":
            dispatcher.utter_message(text="You provided a wrong entity for this type of research. Please rephrase.") 
            return []       
    
        with open(FILE_PATH_RANKING, 'r') as f:
           data = json.load(f)
         
        # if the user refers to a position
        if current_slots.get("last_updated") == "position":
            
            position = current_slots.get("position")
            matching_group = next((group for group in data["groups"] if group["position"] == position), None)
            
            # if the position is in the json file
            if matching_group:
                score = matching_group["score"]
                dispatcher.utter_message(text= f"The score done in {position} position is: {score}.")
                return []
            else:
                dispatcher.utter_message(text= f"There is no score for the {position} position. The positions range from first to fourteenth.")
                return []

        # if the user refers to a group_id
        if current_slots.get("last_updated") == "group_ID":
            
            group_id_value = current_slots.get("group_ID")
            group_id_value = Utils.word_to_number(group_id_value, dispatcher)
            
            # check if the group number is a valid number
            if group_id_value == None:
                return []

            matching_group = next((group for group in data["groups"] if group["id"] == group_id_value), None)
            
            # if the group number is in the json file
            if matching_group:
                score = matching_group["score"]
                dispatcher.utter_message(text= f"The score done by group ({group_id_value}) is: {score}.")
                return []
            else:
                dispatcher.utter_message(text= f"The group {group_id_value} did not take part in the contest. The groups number that participated in the contest range from one to fifteen, excluding eleven.")
                return []

        # if the user refers to a member_group
        if current_slots.get("last_updated") == "member_group":
            
            member_group = current_slots.get("member_group")
            member_group_lower = member_group.lower()
            matching_group = next((group for group in data["groups"] if any(member_group_lower == member.lower() for member in group["group_members"])), None)
            
            # if the member group is in the json file
            if matching_group:
                score = matching_group["score"]
                dispatcher.utter_message(text= f"The score done by {member_group} and the other member of the group is: {score}.")
                return []
            else:
                dispatcher.utter_message(text= f"{member_group} did not take part in the contest. If you provided firstname-surname, please provide lastname-firstname to try a new search.")
                return []

        if current_slots.get("last_updated") == "score":
            dispatcher.utter_message(text= "I am sorry, you asked me about the score made, but you provide the information about the score. Please stop the conversation, then rephrase.")
            return []