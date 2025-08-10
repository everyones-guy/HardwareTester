import React from "react";
import { FaDownload, FaTrashAlt } from "react-icons/fa";
import "./FirmwareTable.css";

interface FirmwareEntry {
    id: string;
    name: string;
    version: string;
    deviceType: string;
    uploadDate: string;
}

interface FirmwareTableProps {
    firmwareList: FirmwareEntry[];
    onDownload?: (id: string) => void;
    onDelete?: (id: string) => void;
}

const FirmwareTable: React.FC<FirmwareTableProps> = ({
    firmwareList,
    onDownload,
    onDelete,
}) => {
    return (
        <div className="firmware-table-wrapper">
            <table className="firmware-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Version</th>
                        <th>Device</th>
                        <th>Uploaded</th>
                        {(onDownload || onDelete) && <th>Actions</th>}
                    </tr>
                </thead>
                <tbody>
                    {firmwareList.length > 0 ? (
                        firmwareList.map((fw) => (
                            <tr key={fw.id}>
                                <td>{fw.name}</td>
                                <td>{fw.version}</td>
                                <td>{fw.deviceType}</td>
                                <td>{fw.uploadDate}</td>
                                {(onDownload || onDelete) && (
                                    <td>
                                        {onDownload && (
                                            <button onClick={() => onDownload(fw.id)} title="Download">
                                                <FaDownload size={16} />
                                            </button>
                                        )}
                                        {onDelete && (
                                            <button onClick={() => onDelete(fw.id)} title="Delete">
                                                <FaTrashAlt size={16} />
                                            </button>
                                        )}
                                    </td>
                                )}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={onDownload || onDelete ? 5 : 4}>No firmware found.</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default FirmwareTable;
