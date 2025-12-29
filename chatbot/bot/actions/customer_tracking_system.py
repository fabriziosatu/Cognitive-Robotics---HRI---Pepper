import json
from .utils import Utils

class TrackingPeople:
    
    def __init__(self, filepath, line_1, line_2, line_3, line_4, dispatcher, entities = None) -> None:
        self.filepath = filepath
        self.line_1 = line_1
        self.line_2 = line_2
        self.line_3 = line_3
        self.line_4 = line_4
        self.foi = {
            "gender": None,
            "bag": None,
            "hat": None,
            "line1_passages": None,
            "line2_passages": None,
            "line3_passages": None,
            "line4_passages": None
        }
        self.nop = 0
        self.entities = entities
        self.dispatcher = dispatcher

    def update(self):
        """
        Update the internal state of the object based on the provided entities.

        This method processes a list of entities and updates the internal state of the object, including lines,
        clothing, and gender information. It iterates through each entity, updating the relevant fields in the 'current_group'dictionary.
        
        In order to properly implement the update logic, taking into account negation, and possible placements in the text of the entities related to line, we have defined two variables to implement this:
        - `current_group` is a dictionary that gets cleared each time clothing or gender-related entities are encountered. This approach ensures correct implementation of logic for negation. The management of fields related to the LINE entities is more complex, but still managed by the dictionary.
        - `line_flag` is a flag used to manage the update of LINE fields, where the logic is more complex than in the previous case. The flag is set to True when updating LINE fields and False when processing other types of entities.
        
        Parameters:
        - None

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """
        # Initialize an empty dictionary to store the current group of entities.
        current_group = dict()  
        # Initialize a flag to track whether LINE fields are being updated.
        line_flag = False

        for entity in self.entities:

            entity_key = entity['entity']
            entity_value = entity['value']
            
            if entity_key in ["passages", "line"]:
                if line_flag is True and entity_key in current_group:
                    if self.__update_line(current_group, update=True) is False:
                        return False
                    key, value = next(reversed(current_group.items()))
                    current_group.clear()
                    if key == "negation":
                        current_group[key] = value                    
                line_flag = True
                neg = False if "negation" in current_group else True
                if not neg:
                    del current_group["negation"]
                current_group[entity_key] = (entity_value, neg)                 
            else:
                if line_flag is True and entity_key == "negation":
                    pass
                else: 
                    if line_flag is True and entity_key != "negation":
                        if self.__update_line(current_group, update=True) is False:
                            return False
                        current_group.clear()
                    line_flag = False
                current_group[entity_key] = entity_value
            
            if all(key in current_group for key in ["passages", "line"]):
                if self.__update_line(current_group, update=True) is False:
                    return False
                current_group.clear()
                line_flag = False

            if not line_flag:
                # Update Clothing Fields
                if "clothing" in entity_key:  
                    self.__update_clothing(current_group=current_group, entity_value=entity_value)
                    current_group.clear()
                # Update Gender Field
                elif "gender" in entity_key:
                    self.__update_gender(current_group=current_group, entity_value=entity_value)
                    current_group.clear()                

        # Update LINE Fields if current_group is not empty - that is, there are LINE entities at the end of the utterance.
        if current_group:
            if self.__update_line(current_group, update=True) is False:
                return False
            current_group.clear()
            line_flag = False
                
        return True 

    def filteringJSON(self):
        """
        Filter the JSON data based on the criteria specified in the 'foi' (fields of interest) dictionary.

        This method reads JSON data from the specified file, filters the data based on gender, clothing items (hat and bag),
        and LINE-related criteria (Line passages). The filtered data is then returned.

        Parameters:
        - None

        Returns:
        - list: A list of filtered people based on the data of interest (doi).

        Raises:
        - None

        """
        doi = dict()    # Data of Interest Dict

        with open(self.filepath, 'r') as f:
            data = json.load(f)
            doi = data["people"]
                    
            # Filter gender, hat, bag
            foi_gender_hat_bag = {key: value for key, value in list(self.foi.items())[0:3] if value is not None}

            if foi_gender_hat_bag:
                doi = [person for person in data['people'] if all(
                    person[key] == value
                    for key, value in foi_gender_hat_bag.items()
                )]

            # Counting line passages for each person
            for person in doi:
                    for line in range(1, 5):
                        person[f"line{line}_passages"] = person["trajectory"].count(line)
                        
            # Filter lines
            foi_line = {key: value for key, value in list(self.foi.items())[3:7] if value is not None}

            if foi_line:
                        
                doi = [person for person in doi if all(
                    (person[key] >= value[0] if value[1] else person[key] < value[0])
                    for key, value in foi_line.items()
                )]
                

            self.nop = len(doi)  # Update the number of people after filtering.

            return doi               

    def __str__(self) -> str:
        people_string = "people of " + self.foi["gender"] + " gender" if self.foi["gender"] is not None else "people"
        output_string = []
        output_string.append("bag" if self.foi["bag"] is True else "no bag" if self.foi["bag"] is False else None)
        output_string.append("hat" if self.foi["hat"] is True else "no hat" if self.foi["hat"] is False else None)
        if self.foi["line1_passages"]:
            passages_string = ("once" if self.foi["line1_passages"][0] == 1 else "twice" if self.foi["line1_passages"][0] == 2 else f'{self.foi["line1_passages"][0]} times')
            line_string = "have crossed at least " + passages_string if self.foi["line1_passages"][1] is True else "have not crossed at least " + passages_string if self.foi["line1_passages"][1] is False else None
            output_string.append(line_string + " the " + self.line_1)
        if self.foi["line2_passages"]:
            passages_string = ("once" if self.foi["line2_passages"][0] == 1 else "twice" if self.foi["line2_passages"][0] == 2 else f'{self.foi["line2_passages"][0]} times')
            line_string = "have crossed at least " + passages_string if self.foi["line2_passages"][1] is True else "have not crossed at least " + passages_string if self.foi["line2_passages"][1] is False else None
            output_string.append(line_string + " the " + self.line_2)  
        if self.foi["line3_passages"]:
            passages_string = ("once" if self.foi["line3_passages"][0] == 1 else "twice" if self.foi["line3_passages"][0] == 2 else f'{self.foi["line3_passages"][0]} times')
            line_string = "have crossed at least " + passages_string if self.foi["line3_passages"][1] is True else "have not crossed at least " + passages_string if self.foi["line3_passages"][1] is False else None
            output_string.append(line_string + " the " + self.line_3) 
        if self.foi["line4_passages"]:
            passages_string = ("once" if self.foi["line4_passages"][0] == 1 else "twice" if self.foi["line4_passages"][0] == 2 else f'{self.foi["line4_passages"][0]} times')
            line_string = "have crossed at least " + passages_string if self.foi["line4_passages"][1] is True else "have not crossed at least " + passages_string if self.foi["line4_passages"][1] is False else None
            output_string.append(line_string + " the " + self.line_4)       
        attributes = [item for item in output_string if item is not None]
        attribute_str = ', '.join(item for item in attributes)
        return f"There are currently {self.nop} {people_string} in the mall that meet the required specifications: {attribute_str}." if attributes else f"There are currently {self.nop} {people_string} in the mall."

    # Private Methods
    def __update_line(self, current_group, update = False):
        """
        Update LINE information based on the provided group and optional parameters.

        Parameters:
        - current_group (dict): The group containing information to update the Lines
        - update (bool): Indicates whether to force an update.

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """

        if update:
            (passages, neg_passages) = (Utils.adverb_to_number(current_group["passages"][0], dispatcher=self.dispatcher), current_group["passages"][1]) if "passages" in current_group else (1, True)
            (line, neg_line) = (current_group["line"][0], current_group["line"][1]) if "line" in current_group else (None, None)
            
            if passages is None:
                return False
            
            if line is not None:
                if line.lower() == self.line_1:
                    self.foi["line1_passages"] = (passages, neg_passages and neg_line)
                elif line.lower() == self.line_2:
                    self.foi["line2_passages"] = (passages, neg_passages and neg_line)
                elif line.lower() == self.line_3:
                    self.foi["line3_passages"] = (passages, neg_passages and neg_line)
                elif line.lower() == self.line_4:
                    self.foi["line4_passages"] = (passages, neg_passages and neg_line)
                else:
                    self.dispatcher.utter_message(text=f"My apologies! I don't know if there is {str(line)} in the shopping mall. I can only check the people passing through {str(self.line_1)}, {str(self.line_2)}, {str(self.line_3)}, and {str(self.line_4)}.")
                    return False
            else:
                self.dispatcher.utter_message(text=f"My apologies! Please point me somewhere to check. Remember, I can only check the people passing through {str(self.line_1)}, {str(self.line_2)}, {str(self.line_3)}, and {str(self.line_4)}.")
                return False
            
            return True
    
    def __update_clothing(self, current_group, entity_value):    
        """
        Update clothing information based on the provided group and entity value.

        Parameters:
        - current_group (dict): The group containing clothing information to update.
        - entity_value (str): The value representing the type of clothing to update.

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """
        neg = not "negation" in current_group
        
        if entity_value in ["hat", "bag"]:
            self.foi[entity_value] = neg
        
    def __update_gender(self, current_group, entity_value):
        """
        Update gender information based on the provided group, entity key, and entity value.

        Parameters:
        - current_group (dict): The group containing gender information to update.
        - entity_value (str): The value representing the gender to update.

        Returns:
        - None

        Raises:
        - None
        """
        neg = not "negation" in current_group

        self.foi["gender"] = entity_value if neg is True else "female" if entity_value == "male" and neg is False else "male"        
        

class TrackingGroups:
    
    def __init__(self, filepath, dispatcher, entities = None) -> None:
        self.filepath = filepath
        self.foi = {
            "score": None
        }
        self.nop = 0
        self.entities = entities
        self.dispatcher = dispatcher
        
    def update(self):
        """
        Update the internal state of the object based on the provided entities.

        This method processes a list of entities and updates the internal state of the object including score information.
        It iterates through each entity, updating the relevant fields in the 'current_group' dictionary.
        
        Parameters:
        - None

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """
        # Initialize an empty dictionary to store the current group of entities.
        current_group = dict()  
        # Initialize a flag to track whether score field are being updated.
        score_flag = False

        for entity in self.entities:

            entity_key = entity['entity']
            entity_value = entity['value']
            
            if entity_key in ["mark"]:
                if score_flag is True and entity_key in current_group:
                    if self.__update_score(current_group, update=True) is False:
                        return False
                    key, value = next(reversed(current_group.items()))
                    current_group.clear()
                    if key == "negation":
                        current_group[key] = value                    
                score_flag = True
                neg = False if "negation" in current_group else True
                if not neg:
                    del current_group["negation"]
                current_group[entity_key] = (entity_value, neg)                 
            else:
                if score_flag is True and entity_key == "negation":
                    pass
                else: 
                    if score_flag is True and entity_key != "negation":
                        if self.__update_score(current_group, update=True) is False:
                            return False
                        current_group.clear()
                    score_flag = False
                current_group[entity_key] = entity_value
            
            if all(key in current_group for key in ["mark"]):
                if self.__update_score(current_group, update=True) is False:
                    return False
                current_group.clear()
                score_flag = False            

        if current_group:
            if self.__update_score(current_group, update=True) is False:
                return False
            current_group.clear()
                
        return True 

    def filteringJSON(self):
        """
        Filter the JSON data based on the criteria specified in the 'foi' (fields of interest) dictionary.

        This method reads JSON data from the specified file, filters the data based on score.
        The filtered data is then returned.

        Parameters:
        - None

        Returns:
        - list: A list of filtered people based on the data of interest (doi).

        Raises:
        - None

        """
        doi = dict()    # Data of Interest Dict

        with open(self.filepath, 'r') as f:
            data = json.load(f)
            doi = data["groups"]
            
            foi_score = {key: value for key, value in list(self.foi.items())[0:1] if value is not None}

            if foi_score:
                doi = [person for person in doi if all(
                    (person[key] >= value[0]) if value[1] is True else (person[key] < value[0]) for key, value in foi_score.items()
                )]

            self.nop = len(doi)  # Update the number of people after filtering.

            return doi 

    def __str__(self) -> str:
        output_string = []
        if self.foi["score"]:
            score_string =("scored at least " if self.foi["score"][1] is True else "scored less than " if self.foi["score"][1] is False else None)
            output_string.append(score_string + str(self.foi["score"][0]) + " points") 
        attributes = [item for item in output_string if item is not None]
        attribute_str = ', '.join(item for item in attributes)
        
        return f"There are {self.nop} groups that have participated in the contets that meet the required specifications: {attribute_str}." if attributes else f"There are {self.nop} groups that have participated in the contets."

    def __update_score(self, current_group, update = False):
        """
        Update score information based on the provided group and optional parameters.

        Parameters:
        - current_group (dict): The group containing information to update the score.
        - update (bool): Indicates whether to force an update.

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """

        if update:
            (mark, neg_mark) = (Utils.word_to_number(current_group["mark"][0], dispatcher=self.dispatcher), current_group["mark"][1]) if "mark" in current_group else (None, None)
            
            if mark is not None:
                self.foi["score"] = (mark, neg_mark)
            else:
                return False
            
            return True