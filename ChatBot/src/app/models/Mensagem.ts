export class Mensagem {

  constructor(sender, text){
        this.sender = sender;
        this.text = text;
  }

  sender: "user" | "bot";
  text: string;
}
