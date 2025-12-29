from word2number import w2n

class Utils:
        
    @staticmethod
    def adverb_to_number(adverb, dispatcher):
        """
        Convert an adverb to a numerical value.

        Parameters:
        - adverb (str): An adverb indicating a frequency, e.g., "once", "twice", "3 times".

        Returns:
        - int or None: The numerical representation of the adverb if conversion is successful, or None if the conversion fails.

        Raises:
        - None

        Example:
        >>> obj = YourClassName()
        >>> obj.__adverb_to_number("once")
        1
        >>> obj.__adverb_to_number("twice")
        2
        >>> obj.__adverb_to_number("3 times")
        3
        >>> obj.__adverb_to_number("forty-one times")
        41
        >>> obj.__adverb_to_number("invalid adverb")
        None
        """
        
        if adverb == "once" or adverb == "one time":
            return 1
        elif adverb == "twice":
            return 2
        elif adverb.endswith(" times"):
            try:
                number = adverb.split(" times")[0]
                return w2n.word_to_num(number)
            except ValueError:
                dispatcher.utter_message(text=f"My apologies! Please, provide a right frequency adverb in the format (once, twice, 'number' times). You provided me the following frequency adverb: {str(adverb)}.")
                return None
        else:
            dispatcher.utter_message(text=f"My apologies! Please, provide a right frequency adverb in the format (once, twice, 'number' times). You provided me the following frequency adverb: {str(adverb)}.")
            return None
    
        
    @staticmethod
    def word_to_number(word, dispatcher):
        try:
            return int(word)  
        except ValueError:
            try:
                return float(word)  
            except ValueError:
                try:
                    return w2n.word_to_num(word)
                except ValueError:
                    dispatcher.utter_message(text=f"My apologies! Please, provide a right number. You provided me: {str(word)}.")
                    return None
