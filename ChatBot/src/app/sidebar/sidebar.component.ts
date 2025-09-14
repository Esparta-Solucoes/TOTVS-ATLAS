import { Component, Input, OnChanges, OnInit } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";
import { Conversa } from "app/models/Conversa";
declare const $: any;
declare interface RouteInfo {
  path: string;
  title: string;
  icon: string;
  class: string;
}
export const ROUTES: RouteInfo[] = [
  { path: "/dashboard", title: "Dashboard", icon: "pe-7s-graph", class: "" },
  { path: "/user", title: "User Profile", icon: "pe-7s-user", class: "" },
  { path: "/table", title: "Table List", icon: "pe-7s-note2", class: "" },
  {
    path: "/typography",
    title: "Typography",
    icon: "pe-7s-news-paper",
    class: "",
  },
  { path: "/icons", title: "Icons", icon: "pe-7s-science", class: "" },
  { path: "/maps", title: "Maps", icon: "pe-7s-map-marker", class: "" },
  {
    path: "/notifications",
    title: "Notifications",
    icon: "pe-7s-bell",
    class: "",
  },
  {
    path: "/upgrade",
    title: "Upgrade to PRO",
    icon: "pe-7s-rocket",
    class: "active-pro",
  },
];

@Component({
  selector: "app-sidebar",
  templateUrl: "./sidebar.component.html",
  styleUrls: ["./sidebar.component.scss"],
})
export class SidebarComponent implements OnInit, OnChanges {
  menuItems: any[];
  @Input() public conversas: Conversa[] = [];

  configuracaoAtiva: boolean = false;
  conversaId: string;

  constructor(private router: Router, private route: ActivatedRoute) {}

  ngOnInit() {
    this.carregarConversas();
    this.route.queryParams.subscribe((params) => {
      this.conversaId = params["conversaId"];
    });
  }

  ngOnChanges() {
    this.carregarConversas();
  }

  isMobileMenu() {
    if ($(window).width() > 991) {
      return false;
    }
    return true;
  }

  public criarConversa() {
    this.carregarConversas();
    const novaConversa = new Conversa();
    novaConversa.id = this.generateGUID();
    this.conversas.unshift(novaConversa);

    localStorage.setItem("conversas", JSON.stringify(this.conversas));

    this.router.navigate(["/chat"], { queryParams: { conversaId: novaConversa.id } });
  }

  public selecionarConversa(id) {
    this.router.navigate(["/chat"], { queryParams: { conversaId: id } });
  }

  public apagarConversa() {
    this.carregarConversas();
    this.conversas = this.conversas.filter((c) => c.id !== this.conversaId);

    localStorage.setItem("conversas", JSON.stringify(this.conversas));

    this.configuracaoAtiva = false;

    if (this.conversas.length === 0) {
      this.router.navigate(["/chat"]);
    } else {
      this.router.navigate(["/chat"], {
        queryParams: { conversaId: this.conversas[0].id },
      });
    }
  }

  public ativarConfiguracao() {
    this.configuracaoAtiva = !this.configuracaoAtiva;
  }

  private carregarConversas() {
    const data = localStorage.getItem("conversas");
    if (data) {
      this.conversas = JSON.parse(data);
    } else {
      this.conversas = [];
    }
  }

  private generateGUID(): string {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
      /[xy]/g,
      function (c) {
        const r = (Math.random() * 16) | 0,
          v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      }
    );
  }
}
