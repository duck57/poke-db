function sortTable(tableId, n) {
var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;

table = document.getElementById(tableId);
switching = true;
dir = "asc";
while (switching) {
    switching = false;
    rows = table.getElementsByTagName("tr");
    for (i = 1; i < (rows.length - 1); i++) {
        shouldSwitch = false;
        x = rows[i].getElementsByTagName("td")[n];
        y = rows[i + 1].getElementsByTagName("td")[n];
                var cmpX=isNaN(parseInt(x.innerHTML))?x.innerHTML.toLowerCase():parseInt(x.innerHTML);
                var cmpY=isNaN(parseInt(y.innerHTML))?y.innerHTML.toLowerCase():parseInt(y.innerHTML);
                cmpX=(cmpX=='-')?0:cmpX;
                cmpY=(cmpY=='-')?0:cmpY;
                var Xint = isNaN(cmpX)
                var Yint = isNaN(cmpY)
        if (!Xint && Yint) {
            shouldSwitch= true;
            break;
        }
        if (dir == "asc") {
            if (cmpX > cmpY) {
                shouldSwitch= true;
                break;
            }
        } else if (dir == "desc") {
            if (cmpX < cmpY) {
                shouldSwitch= true;
                break;
            }
        }
    }
    if (shouldSwitch) {
        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
        switching = true;
        switchcount ++;
    } else {
        if (switchcount == 0 && dir == "asc") {
            dir = "desc";
            switching = true;
        }
    }
}
}