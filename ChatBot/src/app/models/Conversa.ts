import { Mensagem } from "./Mensagem";

export class Conversa {
    constructor(){}

    id: string;
    cod_cliente: string;
    titulo: string;
    mensagens: Mensagem[];
}