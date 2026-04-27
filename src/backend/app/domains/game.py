import random

class Game:
    def __init__(self):
        self.pendu = PenduGame()
        self.game = {
            "party":{
                "state":"STARTED",
                "current_player": 0,
                "current_gain": "",
                "wheel_gains": [50, 50, 100, 100, 200, 200, 300, 400, 500, 'banqueroot'],
                "pendu": self.pendu.get_state()
            },
            "players":[]
        }


    def start_game(self, *names):
        self.game["party"]["state"] = "RUNNING"
        # self.add_player(names,id)
        # self.add_players(self.players)
        self.define_started_player()
        self.pendu.define_split_word()
        self.game["party"]["pendu"] = self.pendu.get_state()
        print(self.game["party"]["current_player"])
        print(self.game["party"]["current_gain"])
        self.controller_round()
        print("manche 1 ternminée")
        self.pendu.define_split_word()
        self.controller_round()
        print("manche 2 terminée")
    
    def end_game(self):
        self.game["party"]["state"] = "FINISHED"

    def add_players(self, players):
        for a in players:     
            player = Player(a)
            self.game["players"].append(player.create_player())

    # def add_player(self, names, id):
    #     for idx, name in enumerate(names):
    #         player = Player(name)
    #         self.game["players"].append(player.create_player(id=idx))

    def turn_wheel(self):
        idx_chosen = random.randint(0,(len(self.game["party"]["wheel_gains"]) - 1))
        gain_chosen = self.game["party"]["wheel_gains"][idx_chosen]
        self.game["party"]["current_gain"] = gain_chosen

    def define_started_player(self):
        idx_chosen = random.randint(0,(len(self.game["players"]) - 1))
        self.game["party"]["current_player"] = idx_chosen

    def current_player(self):
        current_id = self.game["party"]["current_player"]
        current_player = next((p for p in self.game["players"] if p["id"] == current_id))
        return current_player

    def next_player_id(self):
        current_id = self.game["party"]["current_player"]
        len_array_player = len(self.game["players"])
        next_player_id = 0 if current_id == len_array_player - 1 else current_id + 1
        return next_player_id
    
    def next_player_action(self):
        current_id = self.game["party"]["current_player"]
        len_array_player = len(self.game["players"])
        next_player_id = 0 if current_id == len_array_player - 1 else current_id + 1
        self.game["party"]["current_player"] = next_player_id
    
    def display_gagnotte_players(self):
        arr = []
        for player in self.game["players"]:
            parsed = {"joueur":player["name"], "cagnotte":player["cagnotte"]}
            arr.append(parsed)
        return arr


    def controller_round(self):
        # si joueur tombe sur banqueroot -> next
        while self.game["party"]["state"] == "RUNNING":
            # tourner la roue 
            self.turn_wheel()
            if self.game["party"]["current_gain"] == 'banqueroot':
                self.next_player_action()
                continue

            print(self.display_gagnotte_players())
            print("partie en cours", self.game["party"]["pendu"])
            print("gains en cours :", self.game["party"]["current_gain"])
            print("player en cours :", self.current_player()["name"])
            response = self.pendu.find_letter()
            print(response["message"])
            if(response["code_error"] ==  0):
                # le joueur gagne
                # update la cagnotte
                current_player = self.current_player()
                current_player["cagnotte"] += self.game["party"]["current_gain"] * response["nbr_of_letter_found"]
                # update le state
                self.game["players"][current_player["id"]] = current_player
                # relance la boucle
                print(response["word_completed"])
                if(response["word_completed"]):
                    break
                else:
                    continue

            elif(response["code_error"] == 1 or 2):
                # le joueur perd
                # trouver le next player
                next_player_id = self.next_player_id()
                self.game["party"]["current_player"] = next_player_id
                # relancer la boucle
                continue


class Player:
    def __init__(self, player):
        self.pseudo = player["pseudo"]
        self.id = player["id"]
        

    def create_player(self):
        new_player = {
            "id":self.id,
            "name":self.pseudo,
            "cagnotte":0
            }
        return new_player
    

class PenduGame:
    def __init__(self):
        self.data = ["test", "toto", "tata", "lili"]
        self.state = {
            "secret_word":"",
            "parsed_word":""
        }

    def get_state(self):
        return self.state
    
    def define_split_word(self):
        idx_chosen = random.randint(0, len(self.data) - 1)
        word_chosen = self.data[idx_chosen]
        self.state["secret_word"] = word_chosen

        split_word = list(word_chosen)
        idx_random = random.randint(0, len(split_word) - 1)
        letter_chosen = split_word[idx_random]

        parsed_word = []
        letters_position = [i for i, x in enumerate(split_word) if x == letter_chosen]
        for idx, char in enumerate(split_word):
            parsed_word.append(char if idx in letters_position else "_")
        self.state["parsed_word"] = "".join(parsed_word)
    
    def find_letter(self):
        new_char = input("une lettre >")
        idx_finded = [i for i, x in enumerate(list(self.state["secret_word"])) if x == new_char]
        if len(idx_finded) == 0:
            return {
                "success":False, 
                "message":"Mauvaise lettre", 
                "nbr_of_letter_found":0,
                "code_error":1,
                "word_completed": False
                }
        parsed_word_list = list(self.state["parsed_word"])
        for i in idx_finded:
            if parsed_word_list[i] == "_":
                parsed_word_list[i] = new_char
            else:
                return {
                    "success": False, 
                    "message":"Lettre déja utilisée", 
                    "nbr_of_letter_found":0,
                    "code_error":2,
                    "word_completed": False
                    }
        self.state["parsed_word"] = "".join(parsed_word_list)
        return {
            "success": True, 
            "message":"Bonne lettre", 
            "nbr_of_letter_found":len(idx_finded),
            "code_error":0,
            "word_completed": "_" not in self.state["parsed_word"]
            }
            

        

## finir une manche 
## introduire un système de manche (5)
## stocké l'ancien mot pour qu'il ne soit pas réutilisé 
## introduire un système de catégorie aléatoire 
