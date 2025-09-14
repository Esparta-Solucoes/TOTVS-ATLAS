import { Mensagem } from "./../../models/Mensagem";
import { Component, EventEmitter, OnInit, Output } from "@angular/core";
import { FormBuilder, FormGroup, Validators } from "@angular/forms";
import { ActivatedRoute } from "@angular/router";
import { Conversa } from "app/models/Conversa";

declare var $: any;

@Component({
  selector: "footer-cmp",
  templateUrl: "footer.component.html",
  styleUrls: ["./footer.component.scss"],
})
export class FooterComponent implements OnInit {
  test: Date = new Date();

  public form: FormGroup;
  public mensagens: Mensagem[] = [];
  public conversas: Conversa[] = [];

  conversaId: string;

  @Output() atualizaMensagensEmit = new EventEmitter<boolean>();
  @Output() atualizaConversasEmit = new EventEmitter<boolean>();

  constructor(
    private formBuilder: FormBuilder,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.createFormulario();
    this.route.queryParams.subscribe((params) => {
      this.conversaId = params["conversaId"];
      console.log("Conversa ID:", this.conversaId);
    });
  }

  public createFormulario() {
    this.form = this.formBuilder.group({
      input: [{ value: "", disabled: false }, [Validators.required]],
    });
  }

  public enviarMensagem() {
    console.log(this.form.value);

    const mensagem = new Mensagem("user", this.form.value.input);
    this.carregarMensagens(this.form.value.input);
    console.log("Mensagens", this.mensagens);
    this.mensagens.push(mensagem);
    this.conversas.find((c) => c.id === this.conversaId).mensagens =
      this.mensagens;
    localStorage.setItem("conversas", JSON.stringify(this.conversas));
    this.form.get("input")?.patchValue("");

    this.atualizaMensagensEmit.emit(true);

    setTimeout(() => {
      const mensagemBot = new Mensagem(
        "bot",
        "🤖 Esta é uma resposta automática de teste!"
      );
      this.carregarMensagens();
      this.mensagens.push(mensagemBot);
      this.conversas.find((c) => c.id === this.conversaId).mensagens =
        this.mensagens;

      localStorage.setItem("conversas", JSON.stringify(this.conversas));
      this.atualizaMensagensEmit.emit(true);
    }, 1000);
  }

  public carregarMensagens(titulo?) {
    this.conversas = JSON.parse(localStorage.getItem("conversas"));
    const conversaAtual = this.conversas.find((c) => c.id === this.conversaId);
    if (conversaAtual.mensagens) {
        this.mensagens = conversaAtual.mensagens;
    }
    else {
        this.conversas.find((c) => c.id === this.conversaId).titulo = titulo.substring(0, 50);
        this.mensagens = [];
        this.atualizaConversasEmit.emit(true);
    }
  }
}
