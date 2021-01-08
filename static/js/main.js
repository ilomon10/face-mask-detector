const socket = io();

const List = new ListComponent();

socket.on('connect', () => {
  console.log("connected");
  socket.on('new_face', (msg) => {
    const item = List.addItem();
    item.update({ image: `faces/${msg.image}`, timestamp: msg.timestamp });
  });
})

function ListComponent() {
  const self = {
    ListEl: document.getElementById("List"),
    List: []
  };

  const CardEl = self.ListEl.querySelector('.card')
  CardEl.remove();

  self.init = function () { }

  self.addItem = function (state) {
    const Comp = new CardComponent(CardEl.cloneNode(true));
    self.ListEl.prepend(Comp.createNode());
    Comp.update(state);
    self.List.push(Comp);
    return Comp;
  }
  self.clear = function () {
    self.List.forEach((item) => {
      item.element.remove();
    })
    self.List = [];
  }
  return self;
}

function CardComponent(el) {
  const self = {
    state: {
      image: "#",
      timestamp: new Date().getTime(),
    },
    element: el
  }
  self.createNode = function () {
    return self.element;
  };
  self.update = function (state) {
    self.state = {
      ...self.state,
      ...state,
    }
    const img = self.element.getElementsByTagName("img");
    img[0].setAttribute("src", self.state.image);
    const title = self.element.querySelector(".time");
    time = new Date(self.state.timestamp);
    title.innerHTML = `${time.getHours()}:${time.getMinutes()}:${time.getSeconds()} ${time.getDate()}/${time.getMonth()}/${time.getFullYear()}`;
  }
  return self;
}

document.addEventListener('DOMContentLoaded', function () {
  let buttonA = document.querySelector(".button_a");
  let buttonB = document.querySelector(".button_b");
  console.log(buttonA);
  console.log(buttonB);
  buttonA.addEventListener("click", function () {
    console.log("Click");
    buttonB.classList.remove("hide");
    buttonA.setAttribute("disabled", true);
    setTimeout(function () {
      console.log("ready");
      buttonB.removeAttribute("disabled");
    }, 5000);
  })
  buttonB.addEventListener("click", function () {
    console.log("Delete");
    fetch(`http://${window.location.host}/deleteFaces`)
      .then(function (res) {
        console.log(res.status);
        buttonB.classList.add("hide");
        buttonB.setAttribute("disabled", true);
        buttonA.removeAttribute("disabled");
        List.clear();
      });
  })
});
