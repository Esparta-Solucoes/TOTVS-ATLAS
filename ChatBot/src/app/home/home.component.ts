import { Component, ElementRef, Input, OnInit, ViewChild } from "@angular/core";

interface Message {
  sender: "user" | "bot";
  text: string;
}

@Component({
  selector: "app-home",
  templateUrl: "./home.component.html",
  styleUrls: ["./home.component.css"],
})
export class HomeComponent implements OnInit {
  @ViewChild("mensagensPainel") mensagensPainel: ElementRef;

  @Input() messages: Message[] = [
    {
      sender: "user",
      text: "Como estão distribuídos os dados no dashboard? Quais são as categorias com maior representatividade?",
    },
    {
      sender: "bot",
      text: "**📊 Análise de Distribuição dos Dados:**\n\n**Por Região:**\n- Sudeste: 42% (R$ 1.01M)\n- Sul: 28% (R$ 672K)\n- Nordeste: 18% (R$ 432K)\n- Centro-Oeste: 8% (R$ 192K)\n- Norte: 4% (R$ 96K)\n\n**Por Categoria de Produto:**\n- Premium: 35% do volume\n- Standard: 45% do volume\n- Basic: 20% do volume",
    },
    {
      sender: "user",
      text: "Como estão distribuídos os dados no dashboard? Quais são as categorias com maior representatividade?",
    },
    {
      sender: "bot",
      text: "**📊 Análise de Distribuição dos Dados:**\n\n**Por Região:**\n- Sudeste: 42% (R$ 1.01M)\n- Sul: 28% (R$ 672K)\n- Nordeste: 18% (R$ 432K)\n- Centro-Oeste: 8% (R$ 192K)\n- Norte: 4% (R$ 96K)\n\n**Por Categoria de Produto:**\n- Premium: 35% do volume\n- Standard: 45% do volume\n- Basic: 20% do volume",
    },
  ];

  newMessage = "";

  constructor() {}

  ngOnInit() {
    this.messages = JSON.parse(localStorage.getItem("mensagens"));
  }

  sendMessage() {
    if (!this.newMessage.trim()) return;

    this.messages.push({ sender: "user", text: this.newMessage });
    this.newMessage = "";

    setTimeout(() => {
      this.messages.push({
        sender: "bot",
        text: "🤖 Esta é uma resposta automática de teste!",
      });
    }, 1000);
  }

  public atualizarMensagens() {
    this.messages = JSON.parse(localStorage.getItem("mensagens"));
    setTimeout(() => {
      if (this.mensagensPainel && this.mensagensPainel.nativeElement) {
        this.mensagensPainel.nativeElement.scrollTop =
          this.mensagensPainel.nativeElement.scrollHeight;
      }
    }, 0);
  }
}
