import { Component, ElementRef, Input, OnInit, ViewChild } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { Conversa } from "app/models/Conversa";
import { Mensagem } from "app/models/Mensagem";

@Component({
  selector: "app-home",
  templateUrl: "./home.component.html",
  styleUrls: ["./home.component.css"],
})
export class HomeComponent implements OnInit {
  @ViewChild("mensagensPainel") mensagensPainel: ElementRef;

  @Input() messages: Mensagem[] = [
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
  conversaId: string;
  conversas: Conversa[];

  constructor(private route: ActivatedRoute) {}

  ngOnInit() {
    this.route.queryParams.subscribe((params) => {
      this.conversaId = params["conversaId"];
      this.atualizarMensagens();
      console.log("Conversa ID:", this.conversaId);
    });
  }

  sendMessage() {
    if (!this.newMessage.trim()) return;

    this.messages.push({ sender: "user", text: this.newMessage });
    this.newMessage = "";

    // setTimeout(() => {
    //   this.messages.push({
    //     sender: "bot",
    //     text: "🤖 Esta é uma resposta automática de teste!",
    //   });
    // }, 1000);
  }

  public atualizarMensagens() {
    console.log("Atualizando mensagens para a conversa ID:", this.conversaId);

    const conversas: Conversa[] = JSON.parse(localStorage.getItem("conversas"));
    const conversaAtual = conversas.find((c) => c.id === this.conversaId);
    this.messages = conversaAtual.mensagens ?? [];

    if (this.messages.length === 0) this.adicionarMensagemInserirCodCliente();
    else if (!conversaAtual.cod_cliente) this.validarCodCliente();

    setTimeout(() => {
      if (this.mensagensPainel && this.mensagensPainel.nativeElement) {
        this.mensagensPainel.nativeElement.scrollTop =
          this.mensagensPainel.nativeElement.scrollHeight;
      }
    }, 0);
  }

  public atualizarConversas() {
    this.conversas = JSON.parse(localStorage.getItem("conversas"));
  }

  private validarCodCliente() {
    const ultimaMensagem = this.messages[this.messages.length - 1];
    const codClienteRegex = /^\d{6}$/; // Exemplo: código do cliente com 6 dígitos

    if (ultimaMensagem.sender === "user") {
      if (codClienteRegex.test(ultimaMensagem.text)) {
        // Código do cliente válido
        this.atualizarConversas();
        const conversaAtual = this.conversas.find(
          (c) => c.id === this.conversaId
        );
        conversaAtual.cod_cliente = ultimaMensagem.text;
        localStorage.setItem("conversas", JSON.stringify(this.conversas));
      }
      else{
        this.adicionarMensagemInserirCodCliente();
      }
    }
  }

  private adicionarMensagemInserirCodCliente() {
    // setTimeout(() => {
    //   this.messages.push({
    //     sender: "bot",
    //     text: "🤖 Insira um código de cliente válido: ",
    //   });
    // }, 1000);
  }
}
