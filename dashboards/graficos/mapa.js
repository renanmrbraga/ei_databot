/* Geometria e geracao SVG de mapas; sem municipios ou limites fixados por dashboard. */
const DashboardMapa = Object.freeze({
    projetar(lon, lat, {origemLon = -83, origemLat = 14, escala = 13} = {}) {
        return {x: (Number(lon)-origemLon)*escala, y: (origemLat-Number(lat))*escala};
    },
    caixaTexto({x, y, w, h}) {return `${x} ${y} ${w} ${h}`;},
    aproximar(caixa, fator) {
        const cx=caixa.x+caixa.w/2, cy=caixa.y+caixa.h/2;
        return {x:cx-caixa.w*fator/2, y:cy-caixa.h*fator/2, w:caixa.w*fator, h:caixa.h*fator};
    },
    deslocar(caixa, dx, dy, aspecto) {
        if(!Number.isFinite(aspecto) || aspecto<=0) return {...caixa};
        return {...caixa,x:caixa.x-dx/aspecto,y:caixa.y-dy/aspecto};
    },
    contornos(poligonos, {projecao = {}, estilo = () => ({})} = {}) {
        if(!Array.isArray(poligonos)) return "";
        return poligonos.map((poligono) => {
            const visual=estilo(poligono);
            const fill=DashboardFormatacao.esc(visual.fill||"#e9eff0");
            const stroke=DashboardFormatacao.esc(visual.stroke||"#cddbdd");
            return (poligono["anéis"] || poligono.aneis || []).map((anel) => {
                const d=anel.map(([lon,lat], i)=>{
                    const {x,y}=this.projetar(lon,lat,projecao);
                    return `${i?"L":"M"}${x.toFixed(2)} ${y.toFixed(2)}`;
                }).join(" ");
                return `<path d="${d} Z" fill="${fill}" stroke="${stroke}" stroke-width="${visual.espessura ?? 0.65}"/>`;
            }).join("");
        }).join("");
    },
    bolha({x,y,raio=4,cor="#147e80",selecionado=false,dimensao="",valor="",titulo=""} = {}) {
        const esc=DashboardFormatacao.esc;
        return `<g class="map-dot" role="button" tabindex="0" data-filter-dim="${esc(dimensao)}" data-filter-value="${esc(valor)}"><circle cx="${x}" cy="${y}" r="${raio+1.5}" fill="white" stroke="#ffffff" stroke-width="1.3"/><circle cx="${x}" cy="${y}" r="${raio}" fill="${esc(cor)}" fill-opacity="${selecionado?1:.77}" stroke="${selecionado?"#153c57":"white"}" stroke-width="${selecionado?2.5:.5}"/><title>${esc(titulo)}</title></g>`;
    },
});
