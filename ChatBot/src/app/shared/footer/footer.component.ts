import { Mensagem } from "./../../models/Mensagem";
import { Component, EventEmitter, OnInit, Output } from "@angular/core";
import { FormBuilder, FormGroup, Validators } from "@angular/forms";

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

  @Output() atualizaMensagensEmit = new EventEmitter<boolean>();

  constructor(private formBuilder: FormBuilder) {}

  ngOnInit() {
    this.createFormulario();
  }

  public createFormulario() {
    this.form = this.formBuilder.group({
      input: [{ value: "", disabled: false }, [Validators.required]],
    });
  }

  public enviarMensagem() {
    console.log(this.form.value);

    const mensagem = new Mensagem("user", this.form.value.input);
    this.carregarMensagens();
    this.mensagens.push(mensagem);
    localStorage.setItem("mensagens", JSON.stringify(this.mensagens));
    this.form.get("input")?.patchValue("");

    this.atualizaMensagensEmit.emit(true);


    setTimeout(() => {
        const mensagemBot = new Mensagem("bot", "🤖 Esta é uma resposta automática de teste!");
        this.carregarMensagens();
        this.mensagens.push(mensagemBot);
        localStorage.setItem("mensagens", JSON.stringify(this.mensagens));
        this.atualizaMensagensEmit.emit(true);
    }, 1000);

  }

  public carregarMensagens() {
    const data = localStorage.getItem("mensagens");
    if (data) {
      this.mensagens = JSON.parse(data);
    }
  }
}
