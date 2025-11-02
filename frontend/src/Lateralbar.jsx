import {FaHome, FaComment, FaCog} from 'react-icons/fa';

const Lateralbar = ({setPage}) => {
    const elementos = [
        { nombre: 'Inicio', enlace: '/', icon: <FaHome size={24}/> , page: 'docs'},
        { nombre: 'Chat', enlace: '/chat', icon: <FaComment size={24}/> , page: 'chat'},
        { nombre: 'Ajustes', enlace: '/settings', icon: <FaCog size={24}/> , page: 'settings'},
    ]
    return (
        <div className="w-20 bg-gray-800 text-white min-h-screen p-4">
            <h2 className="text-lg font-semibold mb-4"></h2>
            <div className='flex flex-col space-y-12 mt-12'>
                {elementos.map((item, index) => (
                    <div key={item.nombre} className="">
                        <button onClick={() => setPage(item.page)} className="hover:underline">
                            {item.icon}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default Lateralbar;
