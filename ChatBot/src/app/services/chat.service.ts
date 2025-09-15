import { Injectable } from "@angular/core";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Observable } from "rxjs";

@Injectable({
  providedIn: "root",
})
export class ChatService {
  constructor(private http: HttpClient) {}

  enviarMensagem(mensagem: string, codigoCliente: string): Observable<any> {
    const url = "/api/search";

    // Criar query parameters
    const params = new HttpParams()
      .set("query", mensagem)
      .set("cd_cliente", codigoCliente);

    // Passar params no get
    return this.http.get(url, { params, responseType: "text" });
  }
}
